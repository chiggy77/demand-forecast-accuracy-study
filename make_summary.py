import json, docx
from docx.shared import Pt, Cm, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
R = json.load(open('outputs/results.json')); fo = R['fixed_origin']; ro = R['rolling_1m']; best = R['best_fixed_origin']
d = docx.Document(); sec = d.sections[0]; sec.page_width = Cm(21); sec.page_height = Cm(29.7)
sec.left_margin = sec.right_margin = Cm(2); sec.top_margin = Cm(1.6); sec.bottom_margin = Cm(1.5)
st = d.styles['Normal']; st.font.name = 'Calibri'; st.font.size = Pt(10.5); st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Calibri')
BLUE = RGBColor(0x1c, 0x5c, 0xab); GREY = RGBColor(0x52, 0x51, 0x4e)
def para(text='', bold=False, size=None, color=None, after=4, before=0, italic=False):
    p = d.add_paragraph(); p.paragraph_format.space_after = Pt(after); p.paragraph_format.space_before = Pt(before)
    if text:
        r = p.add_run(text); r.bold = bold; r.italic = italic
        if size: r.font.size = Pt(size)
        if color: r.font.color.rgb = color
    return p
def head(t):
    p = para(t, bold=True, size=12, color=BLUE, after=3, before=8); p.paragraph_format.keep_with_next = True
def bullet(label, text):
    p = d.add_paragraph(style='List Bullet'); p.paragraph_format.space_after = Pt(2)
    if label: p.add_run(label).bold = True
    p.add_run(text)
def shade(cell, hexcol):
    tcPr = cell._tc.get_or_add_tcPr(); sh = OxmlElement('w:shd'); sh.set(qn('w:val'), 'clear'); sh.set(qn('w:fill'), hexcol); tcPr.append(sh)
def table(rows, widths):
    t = d.add_table(rows=len(rows), cols=len(rows[0])); t.style = 'Table Grid'
    for i, row in enumerate(rows):
        for j, txt in enumerate(row):
            c = t.cell(i, j); c.width = Cm(widths[j]); p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(0)
            r = p.add_run(txt); r.font.size = Pt(9.5); r.bold = (i == 0)
            if i == 0: shade(c, 'E7F1FB')
    d.add_paragraph().paragraph_format.space_after = Pt(2)
g = R['yoy_growth']; imp = R['forecast_2017_growth_implied']
sn, sg, hw = 'Seasonal naive (same month last year)', 'Seasonal naive x growth', 'Holt-Winters (damped trend, seasonal)'
para('Demand forecast accuracy study: which simple method plans best, and why does it miss?', bold=True, size=17, color=BLUE, after=2)
para('Personal project, October 2026  |  Chirag Arora  |  Python (Pandas, statsmodels), WAPE and bias', size=9.5, color=GREY, after=6)
head('Goal and data')
para(f"I mimicked a monthly demand-planning cycle: forecast {R['series']} store-item series, measure accuracy with WAPE and bias, and look for the root causes of the misses. Data: the public Store Item Demand Forecasting dataset ({R['rows']:,} daily sales rows, 10 stores x 50 items, 2013-2017), aggregated to months. I trained on 2013-2016 and forecast all 12 months of 2017. The data is very smooth and may be synthetic, so real accuracy would be lower.", after=2)
head('Methods compared (error at store x item x month level)')
rows = [['Method', 'WAPE', 'Bias', 'WAPE at total level']]
for k in fo: rows.append([k, f"{fo[k]['sku_market']:.1%}", f"{fo[k]['bias']:+.1%}", f"{fo[k]['total']:.1%}"])
table(rows, [8.2, 2.4, 2.4, 4.0])
head('What I found')
bullet('Seasonality is the biggest lever. ', f"Repeating last month gives {fo['Naive (last month)']['sku_market']:.1%} error; repeating the same month last year gives {fo[sn]['sku_market']:.1%}. Holt-Winters is best at {fo[hw]['sku_market']:.1%}, only {100*(fo[sn]['sku_market']-fo[hw]['sku_market']):.1f} points better than the simple seasonal method.")
bullet('Root cause of the bias: growth slowed. ', f"Sales grew {g['2016']:.1%} in 2016 but only {g['2017']:.1%} in 2017. Scaling last year by recent growth implied +{imp[sg]:.1%} and over-forecast by {fo[sg]['bias']:+.1%}; plain seasonal naive implied {imp[sn]:.1%} and under-forecast by {fo[sn]['bias']:+.1%}; Holt-Winters implied +{imp[hw]:.1%} (bias {fo[hw]['bias']:+.1%}). Extrapolating growth needs a business check.")
bullet('Not every method adds value. ', f"Compared with the naive forecast one month ahead, seasonal naive x growth reduces error by {R['fva_vs_naive_rolling'][sg]*100:.1f} points, while the 3-month moving average is {abs(R['fva_vs_naive_rolling']['Moving average (3 months)'])*100:.1f} points worse than naive.")
bullet('No small group explains the error. ', f"The 10% of series with the largest error account for {R['error_concentration']['top_10pct_series_share_of_error']:.0%} of it (they hold {R['volume_concentration']['top_10pct_series_share_of_volume']:.0%} of volume), and all stores sit between {min(R['wape_by_store'].values()):.1%} and {max(R['wape_by_store'].values()):.1%}. Gains must come from assumptions, not from fixing a few items.")
bullet('Aggregation helps a little. ', f"The best method's error falls from {fo[hw]['sku_market']:.1%} per store-item to {fo[hw]['total']:.1%} for the total.")
d.add_picture('outputs/chart_method_accuracy.png', width=Cm(12.5)); d.paragraphs[-1].alignment = 1
d.add_picture('outputs/chart_actual_vs_forecast_2017.png', width=Cm(12.5)); d.paragraphs[-1].alignment = 1
head('How I would use this in a planning team')
bullet('', 'Report WAPE and bias every month, by market and by item, and write one line on the cause of each large variance.')
bullet('', 'Keep a seasonal baseline and measure whether each judgement adjustment (forecast value added) improves it.')
bullet('', 'Review trend assumptions with Marketing before applying growth factors, and track bias by quarter.')
head('Limits')
bullet('', 'The data has no promotions, new product launches or product life cycles, so it does not test the hardest parts of beauty demand planning. One test year, untuned models, no inventory or service-level view.')
bullet('', 'The method accuracy figures describe this dataset only. I built the project with Claude as a coding assistant and checked the results myself; six automated tests cover the metrics and methods.')
para('Source: public GitHub copy of the Kaggle Store Item Demand Forecasting Challenge data (jgonzalezab/Store-Item-Demand-Forecasting, Data/train.csv). Code, tests and outputs are in the project folder.', size=9, italic=True, color=GREY, before=6)
d.save('Chirag_Arora_Demand_Forecast_Accuracy_Study.docx')
