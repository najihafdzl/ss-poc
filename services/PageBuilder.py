import uuid
import random
import os
import json

from utils.Config import Config
from utils.Tools import _warn

class PageBuilder:
    serviceIcon = {
        'ec2': 'server',
        'rds': 'database',
        's3': 'hdd',
        'iam': 'users',
        'guardduty': 'shield-alt',
        'opensearch': 'warehouse'
    }

    pageTemplate = {
        'header.precss': 'header.precss.template.html',
        'header.postcss': 'header.postcss.template.html',
        'sidebar.precustom': 'sidebar.precustom.template.html',
        'sidebar.postcustom': 'sidebar.postcustom.template.html',
        'breadcrumb': 'breadcrumb.template.html',
        'footer.prejs': 'footer.prejs.template.html',
        'footer.postjs': 'footer.postjs.template.html',
    }

    isHome = False

    def __init__(self, service, reporter, services, regions):
        self.service = service
        self.services = services
        self.regions = regions
        self.reporter = reporter

        self.idPrefix = self.service + '-'

        self.js = []
        self.jsLib = []
        self.cssLib = []
        
    def getHtmlId(self, el=''):
        o = uuid.uuid4().hex
        el = el or o[0:11]
        return self.idPrefix + el

    def buildPage(self):
        self.init()

        output = []
        output.append(self.buildHeader())
        output.append(self.buildNav())
        output.append(self.buildBreadcrumb())
        output.append(self.buildContentSummary())
        output.append(self.buildContentDetail())
        output.append(self.buildFooter())

        finalHTML = ""
        for arrayOfText in output:
            if arrayOfText:
                finalHTML += "\n".join(arrayOfText)

        with open(Config.DIR_HTML + '/' + self.service + '.html', 'w') as f:
            f.write(finalHTML)
    
    def init(self):
        self.template = 'default'
    
    def buildContentSummary(self):
        method = 'buildContentSummary_' + self.template
        if hasattr(self, method):
            return getattr(self, method)()
        else:
            cls = self.__class__.__name__
            print("[{}] Template for ContentSummary not found: {}".format(cls, method))
    
    def buildContentDetail(self):
        method = 'buildContentDetail_' + self.template
        if hasattr(self, method):
            return getattr(self, method)()
        else:
            cls = self.__class__.__name__
            print("[{}] Template for ContentDetail not found: {}".format(cls, method))
            
    def generateRowWithCol(self, size=12, items=[], rowHtmlAttr=''):
        output = []
        output.append("<div class='row' {}>".format(rowHtmlAttr))

        _size = size
        for ind, item in enumerate(items):
            if isinstance(size, list):
                i = ind % len(size)
                _size = size[i]
            output.append(self.generateCol(_size, item))
        output.append("</div>")

        return "\n".join(output)
        
    def generateCol(self, size=12, item=[]):
        output = []
        if not item:
            output.append("</div><div class='row'>")
        else:
            html, divAttr = item
            output.append("<div class='col-md-{}' {}>".format(size, divAttr))
            output.append(html)
            output.append("</div>")
        return "\n".join(output)
        
    def generateCard(self, pid, html, cardClass='warning', title='', titleBadge='', collapse=False, noPadding=False):
        output = []

        lteCardClass = '' if not cardClass else "card-{}".format(cardClass)
        defaultCollapseClass = "collapsed-card" if collapse == 9 else ""
        defaultCollapseIcon = "plus" if collapse == 9 else "minus"

        output.append("<div id='{}' class='card {} {}'>".format(pid, lteCardClass, defaultCollapseClass))

        if title:
            output.append("<div class='card-header'><h3 class='card-title'>{}</h3>".format(title))

            if collapse:
                output.append("<div class='card-tools'><button type='button' class='btn btn-tool' data-card-widget='collapse'><i class='fas fa-{}'></i></button></div>".format(defaultCollapseIcon))

            if titleBadge:
                output.append(titleBadge)

            output.append("</div>")

        noPadClass = 'p-0' if noPadding else ''

        output.append("<div class='card-body {}'>".format(noPadClass))
        output.append(html)
        output.append("</div>")
        output.append("</div>")
        return "\n".join(output)
        
    def generateCategoryBadge(self, category, addtionalHtmlAttr):
        validCategory = ['R', 'S', 'O', 'P', 'C', 'T']
        colorByCategory = ['info', 'danger', 'primary', 'success', 'warning', 'info']
        nameByCategory = ['Reliability', 'Security', 'Operation Excellence', 'Performance Efficiency', 'Cost Optimization', 'Text']
        if category not in validCategory:
            category = 'X'
            color = 'info'
            name = 'Suggestion'
        else:
            indexOf = validCategory.index(category)
            color = colorByCategory[indexOf]
            name = nameByCategory[indexOf]

        return "<span class='badge badge-{}', {}>{}</span>".format(color, addtionalHtmlAttr, name)
        
    def generatePriorityPrefix(self, criticality, addtionalHtmlAttr):
        validCategory = ['I', 'L', 'M', 'H']
        colorByCategory = ['info', 'primary', 'warning', 'danger']
        iconByCategory = ['info-circle', 'eye', 'exclamation-triangle', 'ban']

        criticality = criticality if criticality in validCategory else validCategory[0]

        indexOf = validCategory.index(criticality)
        color = colorByCategory[indexOf]
        icon = iconByCategory[indexOf]

        return "<span class='badge badge-{}' {}><i class='icon fas fa-{}'></i></span>".format(color, addtionalHtmlAttr, icon)

    def generateSummaryCardContent(self, summary):
        output = []

        resources = summary['__affectedResources']
        resHtml = []
        for region, resource in resources.items():
            items = []
            resHtml.append(f"<dd>{region}: ")
            for identifier in resource:
                items.append(f"<a href='#{self.service}-{identifier}'>{identifier}</a>")
            resHtml.append(" | ".join(items))
            resHtml.append("</dd>")

        output.append("<dl><dt>Description</dt><dd>" + summary['^description'] + "</dd><dt>Resources</dt>" + "".join(resHtml))

        hasTags = self.generateSummaryCardTag(summary)
        if len(hasTags.strip()) > 0:
            output.append(f"<dt>Label</dt><dd>{hasTags}</dd>")

        if summary['__links']:
            output.append("<dt>Recommendation</dt><dd>" + "</dd><dd>".join(summary['__links']) + "</dd>")

        output.append("</dl>")

        return "\n".join(output)
        
    def generateDonutPieChart(self, datasets, idPrefix='', typ='doughnut'):
        htmlId = idPrefix + typ + str(uuid.uuid1(self.__class__))
        output = []
        output.append("<div class='chart'><canvas id='{}' style='min-height: 250px; height: 250px; max-height: 250px; max-width: 100%;'></canvas>\</div>".format(htmlId))

        labels, enriched = self._enrichDonutPieData(datasets)

        self.addJS("var donutPieChartCanvas = $('#{}').get(0).getContext('2d'); var donutPieData = {{labels: {},datasets: [{}]}}".format(htmlId, json.dumps(labels), json.dumps(enriched)))
        self.addJS("var donutPieOptions= {{maintainAspectRatio : false,responsive : true}}; new Chart(donutPieChartCanvas, {{type: '{}', data: donutPieData, options: donutPieOptions}})".format(type))

        return '\n'.join(output)
        
    def generateBarChart(self, labels, datasets, idPrefix = ''):
        id = idPrefix + 'bar' + str(uuid.uuid1())

        output = []
        output.append("<div class='chart'><canvas id='" + id + "' style='min-height: 250px; height: 250px; max-height: 250px; max-width: 100%;'></canvas></div>")

        enriched = self._enrichChartData(datasets)

        self.addJS("var areaChartData = {labels: " + json.dumps(labels) + ", datasets: " + json.dumps(enriched) + "}")
        self.addJS("var barChartData = $.extend(true, {}, areaChartData); var stackedBarChartCanvas = $('#" + id + "').get(0).getContext('2d'); var stackedBarChartData = $.extend(true, {}, barChartData)")
        
        self.addJS("""
        var stackedBarChartOptions = {
          responsive              : true,
          maintainAspectRatio     : false,
          scales: {
            xAxes: [{
              stacked: true,
            }],
            yAxes: [{
              stacked: true
            }]
          },
         onClick: function(e, i){
            checkCtrl = $('#checkCtrl')
            var v = i[0]['_model']['label'];
            if(typeof v == 'undefined')
                return
            curVal = checkCtrl.val()
            idx = curVal.indexOf(v)
            if (idx == -1){
                curVal.push(v)
            }else{
                curVal.splice(idx, 1);
            }
            checkCtrl.val(curVal).trigger('change')
        }
    }
            new Chart(stackedBarChartCanvas, {
                type: 'bar',
                data: stackedBarChartData,
                options: stackedBarChartOptions
            })""")
        
        return "\n".join(output)
        
    def generateSummaryCardTag(self, summary):
        text = ''
        text += self._generateSummaryCardTagHelper(summary.get('downtime', False), 'Have Downtime')
        text += ' ' + self._generateSummaryCardTagHelper(summary.get('needFullTest', False), 'Testing Required')
        text += ' ' + self._generateSummaryCardTagHelper(summary.get('slowness', False), 'Performance Impact')
        text += ' ' + self._generateSummaryCardTagHelper(summary.get('additionalCost', False), 'Cost Incurred')

        return text
        
    def _generateSummaryCardTagHelper(self, flag, text):
        if flag == False:
            return ''
        
        strx = text
        color = 'warning'
        if flag < 0:
            strx += " (maybe)"
            color = 'info'
            
        return f"<span class='badge badge-{color}'>{strx}</span>"
        
    def _enrichDonutPieData(self, datasets):
        label = []
        arr = {
            'data': [],
            'backgroundColor': []
        }
        
        idx = 0
        for key, num in datasets.items():
            label.append(key)
            arr['data'].append(num)
            arr['backgroundColor'].append(self._randomHexColorCode(idx))
            
            idx += 1
            
        return [label, arr]
        
    def _enrichChartData(self, datasets):
        arr = []
        idx = 0
        for key, num in datasets.items():
            arr.append({
                'label': key,
                'backgroundColor': self._randomRGB(idx),
                'data': num
            })
            idx += 1

        return arr
        
    def _randomRGB(self, idx):
        r1Arr = [226, 168, 109, 80 , 51 , 60 , 70 , 89 , 108]
        r2Arr = [124, 100, 75 , 63 , 51 , 78 , 105, 158, 212]
        r3Arr = [124, 100, 75 , 63 , 51 , 75 , 100, 148, 197]
        
        if idx >= len(r1Arr):
            r1 = random.randint(1,255)
            r2 = random.randint(1,255)
            r3 = random.randint(1,255)    
        else:
            r1 = r1Arr[idx]
            r2 = r2Arr[idx]
            r3 = r3Arr[idx]
        
        return "rgba({}, {}, {}, 1)".format(r1, r2, r3)
        
    def _randomHexColorCode(self, idx):
        color = ["#e27c7c", "#a86464", "#6d4b4b", "#503f3f", "#333333", "#3c4e4b", "#466964", "#599e94", "#6cd4c5"]
        if idx >= len(color):
            return '#' + str(hex(random.randint(0, 0xFFFFFF))).lstrip('0x').rjust(6, '0')
        else:
            return color[idx]

    def generateTitleWithCategory(self, count, title, category, color='info'):
        if not category:
            return title
        return f"{count}. {title} <span class='detailCategory' data-span-category='{category}'></span>"
        
    def generateTable(self, resource):
        output = []
        for check, attr in resource.items():
            criticality = attr['criticality']
            checkPrefix = ''
            if criticality == 'H':
                checkPrefix = "<i style='color: #dc3545' class='icon fas fa-ban'></i> "
            elif criticality == 'M':
                checkPrefix = "<i style='color: #ffc107' class='icon fas fa-exclamation-triangle'></i> "

            output.append("<tr>")
            output.append("<td>{}{}</td>".format(checkPrefix, check))
            output.append("<td>{}</td>".format(attr['value']))
            output.append("<td>{}</td>".format(attr['shortDesc']))
            output.append("</tr>")

        return "\n".join(output)
        
    def _getTemplateByKey(self, key):
        path = Config.DIR_TEMPLATE + '/' + self.pageTemplate[key]
        
        if os.path.exists(path):
            return path
        else:
            _warn(path + ' does not exists')
            ## <TODO>
            # debug_print_backtrace()
    
    def buildHeader(self):
        output = []
        #file_get_pre_css
        headerPreCSS = open(self._getTemplateByKey('header.precss'), 'r').read()
        headerPreCSS = headerPreCSS.replace('{$ADVISOR_TITLE}', Config.ADVISOR['TITLE'])
        headerPreCSS = headerPreCSS.replace('{$SERVICE}', self.service.upper())
        output.append(headerPreCSS)

        if self.cssLib:
            for lib in self.cssLib:
                output.append("<link ref='stylesheet' href='{}'>".format(lib))

        #file_get_post_css
        headerPostCSS = open(self._getTemplateByKey('header.postcss'), 'r').read()
        output.append(
            headerPostCSS.replace('{$ADVISOR_TITLE}', Config.ADVISOR['TITLE'])
        )

        return output
    
    def buildFooter(self):
        output = []
        #file_get_template preInlineJS
        preJS = open(self._getTemplateByKey('footer.prejs'), 'r').read()
        preJS = preJS.replace('"', "'")

        ADMINLTE_VERSION = Config.ADMINLTE['VERSION']
        ADMINLTE_DATERANGE = Config.ADMINLTE['DATERANGE']
        ADMINLTE_URL = Config.ADMINLTE['URL']
        ADMINLTE_TITLE = Config.ADMINLTE['TITLE']

        PROJECT_TITLE = Config.ADVISOR['TITLE']
        PROJECT_VERSION = Config.ADVISOR['VERSION']
        x = eval("f'{preJS}'")
        output.append(x)

        if self.jsLib:
            for lib in self.jsLib:
                output.append(f"<script src='{lib}'></script>")

        if self.js:
            inlineJS = '; '.join(self.js)
            output.append(f"<script>$(function(){{{inlineJS}}})</script>")

        #file_get_template postInlineJS
        postJS = open(self._getTemplateByKey('footer.postjs'), 'r').read()
        output.append(postJS)

        return output    
        
    def buildBreadcrumb(self):
        output = []
        breadcrumb = open(self._getTemplateByKey('breadcrumb'), 'r').read()
        breadcrumb = breadcrumb.replace('{$SERVICE}', self.service.upper())
        output.append(breadcrumb)
           
        return output
        
    def buildNav(self):
        ISHOME = 'active' if self.isHome else ''

        output = []
        #file_getsidebar
        sidebarPRE = open(self._getTemplateByKey('sidebar.precustom'), 'r').read()
        sidebarPRE = sidebarPRE.replace('{$ADVISOR_TITLE}', Config.ADVISOR['TITLE'])
        sidebarPRE = sidebarPRE.replace('{$ISHOME}', ISHOME)
        output.append(sidebarPRE)

        arr = self.buildNavCustomItems()
        output.append("\n".join(arr))

        sidebarPOST = open(self._getTemplateByKey('sidebar.postcustom'), 'r').read()
        output.append(sidebarPOST)

        return output
    
    def buildNavCustomItems(self):
        services = self.services
        activeService = self.service

        output = []
        output.append("<li class='nav-header'>Services</li>")

        for name, count in services.items():
            if name == activeService:
                class_ = 'active'
            else:
                class_ = ''
            icon = self._navIcon(name)

            _count = count
            if name == 'guardduty':
                _count = ''

            output.append("<li class='nav-item'>\n"
                          "<a href='{}.html' class='nav-link {}'>\n"
                          "<i class='nav-icon fas fa-{}'></i>\n"
                          "<p>{} <span class='badge badge-info right'>{}</span></p>\n"
                          "</a>\n"
                          "</li>".format(name, class_, icon, name.upper(), _count))

        return output
        
    def _navIcon(self, service):
        return self.serviceIcon.get(service, 'cog')
        
    def addJS(self, js):
        self.js.append(js)
        
    def addJSLib(self, js):
        self.jsLib.append(js)
        
    def addCSSLib(self, css):
        self.cssLib.append(css)
        
    def checkIsLowHangingFruit(self, attr):
        if attr['downtime'] == 0 and attr['additionalCost'] == 0 and attr['needFullTest'] == 0:
            return True
        else:
            return False
    
    def buildContentSummary_default(self):
        output = []

        ## Chart Building
        summary = self.reporter.cardSummary
        regions = self.regions
        labels = []
        dataSets = {}
        for label, attrs in summary.items():
            labels.append(label)
            res = attrs['__affectedResources']
            for region in regions:
                cnt = 0
                if res[region]:
                    cnt = len(res[region])
                dataSets.setdefault(region, []).append(cnt)
        
        pid=self.getHtmlId('SummaryChart')
        html = self.generateBarChart(labels, dataSets)
        card = self.generateCard(pid, html, cardClass='warning', title='Summary', titleBadge='', collapse=True, noPadding=False)
        items = [[card, '']]
        output.append(self.generateRowWithCol(size=12, items=items, rowHtmlAttr="data-context='summaryChart'"))
        ## Chart completed

        ## Filter
        filterTitle = "<i class='icon fas fa-search'></i> Filter"
        filterByCheck = self.generateFilterByCheck(labels)
        filterRow = self.generateRowWithCol(size=[6, 6, 12], items=self.addSummaryControl_default(), rowHtmlAttr="data-context='summary-control'")

        output.append(self.generateCard(pid='summary-control', html=filterByCheck + filterRow, cardClass='info', title=filterTitle, titleBadge='', collapse=False, noPadding=False))
        
        ## SummaryCard Building
        items = []
        for label, attrs in summary.items():
            body = self.generateSummaryCardContent(attrs)

            badge = self.generatePriorityPrefix(attrs['criticality'], "style='float:right'") + ' ' + self.generateCategoryBadge(attrs['__categoryMain'], "style='float:right'")
            card = self.generateCard(pid=self.getHtmlId(label), html=body, cardClass='', title=label, titleBadge=badge, collapse=9, noPadding=False)
            divHtmlAttr = "data-category='" + attrs['__categoryMain'] + "' data-criticality='" + attrs['criticality'] + "'"

            if self.checkIsLowHangingFruit(attrs):
                divHtmlAttr += " data-lhf=1"

            items.append([card, divHtmlAttr])

        output.append(self.generateRowWithCol(size=4, items=items, rowHtmlAttr="data-context='summary'"))
        return output
        
    def buildContentDetail_default(self):
        output = []
        output.append('<h5 class="mt-4 mb-2">Detail</h5>')

        details = self.reporter.getDetail()
        count = 1
        previousCategory = ""
        for region, lists in details.items():
            items = []
            output.append("<h6 class='mt-4 mb-2'>{}</h6>".format(region))
            for identifierx, attrs in lists.items():
                tab = []
                identifier = identifierx
                category = ''
                checkIfCategoryPresent = identifierx.split('::')
                if len(checkIfCategoryPresent) == 2:
                    category, identifier = checkIfCategoryPresent
                    if not previousCategory:
                        previousCategory = category

                tab.append("<table class='table table-sm'><thead><tr>")
                tab.append("<th scole='col'>Check</th><th scole='col'>Current Value</th><th scole='col'>Recommendation</th>")
                tab.append("</tr></thead><tbody>")
                tab.append(self.generateTable(attrs))
                tab.append("</tbody></table>")
                tab = "\n".join(tab)

                if previousCategory != category and category != '' and count % 2 == 0:
                    items.append([])

                item = self.generateCard(pid=self.getHtmlId(identifierx), html=tab, cardClass='warning', title=self.generateTitleWithCategory(count, identifier, category), titleBadge='', collapse=False, noPadding=True)
                items.append([item, ''])

                previousCategory = category
                count += 1

            output.append(self.generateRowWithCol(size=6, items=items, rowHtmlAttr="data-context=detail"))
        
        str = """
$('span.detailCategory').each(function(){
  var t = $(this);
  t.parent().parent().append("<span class='badge badge-info' style='float:right; line-height:15px'>"+t.data('span-category')+"</span>");
})
"""
        self.addJS(str)
        
        return output
        
    def generateFilterByCheck(self, labels):
        output = []

        opts = []
        for label in labels:
            opts.append("<option value='{}'>{}</option>".format(label, label))

        options = ''.join(opts)

        str = """
<div class='col-md-12'>
<div class="form-group">
	<label>Checks</label>
	<div class="select2-purple">
	<select id='checkCtrl' class="select2" multiple data-placeholder="Select checks..." data-dropdown-css-class="select2-purple" style="width: 100%;">
		{}
	</select>
	</div>
</div>
</div>
""".format(options)

        return str
        
    def addSummaryControl_default(self):
        jsServIdPrefix = "#" + self.service + '-'

        output = []
        output.append('')

        items = []
        str = """<div class="form-group">
  <label>Pillar</label>
  <select id='filter-pillar' class="form-control">
    <option value='-' selected>All</option>
    <option value='O'>Operation Excellence</option>
    <option value='R'>Reliablity</option>
    <option value='S'>Security</option>
    <option value='P'>Performance Efficiency</option>
    <option value='C'>Cost Optimization</option>
    <option value='T'>*Text*</option>
  </select>
</div>"""
        items.append([str, ''])
    
        str = """
<div class="form-group">
  <label>Criticality</label>
  <select id='filter-critical' class="form-control">
    <option value='-' selected>All</option>
    <option value='H'>High</option>
    <option value='M'>Medium</option>
    <option value='L'>Low</option>
    <option value='I'>Informational</option>
  </select>
</div>
"""
        items.append([str, ''])

        str = """
<div class='col-md-12' >
  <div class='row'>
    <div class='col-md-4'>
      <div class="form-group">
          <div class="icheck-success d-inline">
              <input type="checkbox" id="cbLowHangingFruit">
              <label for="cbLowHangingFruit">Show low hanging fruit(s) only</label>
          </div>
      </div>
    </div>
    <div class='col-md-4'>
      <div class="form-group clearfix">
        <div class="icheck-success d-inline">
          <input type="radio" id="radio_cs1" name=radio_cs value='expand'>
          <label for="radio_cs1">Expand / </label>
        </div><div class="icheck-success d-inline">
          <input type="radio" id="radio_cs2" name=radio_cs value='collapse' checked>
          <label for="radio_cs2">Hide all cards</label>
        </div>
      </div>
    </div>
  </div>
</div>
"""
        items.append([str, ''])
        
        js = """
$('.select2').select2()
var si = $('div[data-context="summary"] div[data-category]');
var cards = $('[data-context="summary"] div.col-md-4')
$('input[name=radio_cs]').change(function(){
  var v = $(this).val()
  var i = cards.find('button > i')
  if (v == 'expand') {
    cards.find('.collapsed-card').removeClass('collapsed-card')
    cards.find('div.card-body').show()
    i.removeClass('fa-plus').addClass('fa-minus')
  }else{
    tmp = $('[data-context="summary"] div.col-md-4 > div:not(.collapsed-card)')
    tmp.addClass('collapsed-card')
    cards.find('div.card-body').hide()
    i.removeClass('fa-minus').addClass('fa-plus')
  }
})
$('#filter-critical, #filter-pillar, #checkCtrl, #cbLowHangingFruit').change(function(){
var cb_lhf_on = $("#cbLowHangingFruit").is(':checked')
var pv = $('#filter-pillar').val();
var fc = $('#filter-critical').val();
var tiArray = $('#checkCtrl').val();
var s = '';
if(pv != '-') s += '[data-category="'+pv+'"]';
if(fc != '-') s += '[data-criticality="'+fc+'"]';
if(tiArray.length > 0){
	si.hide()
	$.each(tiArray, function(k, v){"""
        txt = "id = \"{}\" + v;".format(jsServIdPrefix)
        js += txt
        js += """$(id).parent().addClass('showLater');
	})
	if(s.length > 0){
		$('div[data-context="summary"] .showLater'+s+'').show()
	}else{
		$('.showLater').show()
	}
	$('.showLater').removeClass('showLater')
}else if(s.length == 0){
  si.show();
}else{
  si.hide();
  $('div[data-context="summary"] div'+s+'').show()
}
$('[data-context="summary"] .col-md-4:visible').addClass('showLater2')
if(cb_lhf_on == true){
  $('.showLater2').hide()
  $('.showLater2[data-lhf=1]').show()
  $('.showLater2').removeClass('showLater2')
}
})
"""
        self.addJS(js)
        return items