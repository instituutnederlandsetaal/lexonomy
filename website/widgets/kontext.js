window.Kontext={};

Kontext.extendDocspec=function(docspec, xema){
  if(kontext.corpus) {
    if(!subbing[xema.root]) {
      var elSpec=docspec.elements[xema.root];
      var incaption=elSpec.caption;
      elSpec.caption=function(jsMe){
        var cap="";
        cap="<span class='lexonomyKontextCaption' onclick='Xonomy.notclick=true; Kontext.menuRoot(\""+jsMe.htmlID+"\")'>▼</span>";
        if(typeof(incaption)=="function") cap=incaption(jsMe)+cap;
        if(typeof(incaption)=="string") cap=incaption+cap;
        return cap;
      };
    }
  }
};

Kontext.menuRoot=function(htmlID, additional=false){
  var html="<div class='menu'>";
  if (!additional) {
    if(kontext.container) {
      html+="<div class='menuItem' onclick='Kontext.menuExamples(\""+htmlID+"\", \"layby\")'>";
        html+="<span class='icon'><img src='../../../furniture/kontext.png'/></span> ";
        html+="Find examples <span class='techno'><span class='punc'>&lt;</span><span class='elName'>"+kontext.container+"</span><span class='punc'>&gt;</span></span>";
      html+="</div>";
    }
  }
  if (additional) {
    var headword = encodeURIComponent(Kontext.getSearchword(htmlID));
  } else {
    var headword = encodeURIComponent(Kontext.getHeadword());
  }
  if(headword) {
    html+="<div class='menuItem')'>";
        html+="<a target='kontext' href='/"+dictId+"/kontext/conc?lemma="+headword+"&redir=1'>";
        html+="<span class='icon'><img src='../../../furniture/kontext.png'/></span> ";
        html+="Show concordance";
      html+="</a>";
    html+="</div>";
  }
  html+="</div>";
  Xonomy.makeBubble(html); //create bubble
  Xonomy.showBubble($("#"+htmlID+" > .inlinecaption")); //anchor bubble to opening tag
};
Kontext.getHeadword=function(){
  var $xml=$($.parseXML(Xonomy.harvest()));
  var hwd=$xml.find(titling.headword).html();
  if(!hwd) hwd="";
  return hwd;
};
Kontext.getSearchword=function(elementID){
  return Xonomy.harvestElement(document.getElementById(elementID)).getText();
};
Kontext.menuExamples=function(htmlID, param){
  if(param=="layby") Kontext.htmlID=null; else  Kontext.htmlID=htmlID;
  Xonomy.makeBubble(Kontext.boxExamples()); //create bubble
  $("input[name=kontextsearchtype]").on("click", function() {
    var val = $(this).val() == "kontextsimple"
    $("#kontextsimple").nextAll("input").first().prop("disabled", !val)
    $("#kontextcql").nextAll("input").first().prop("disabled", val)
  })
  if(Xonomy.lastClickWhat=="openingTagName") Xonomy.showBubble($("#"+htmlID+" > .tag.opening > .name")); //anchor bubble to opening tag
  else if(Xonomy.lastClickWhat=="closingTagName") Xonomy.showBubble($("#"+htmlID+" > .tag.closing > .name")); //anchor bubble to closing tag
  else Xonomy.showBubble($("#"+htmlID));
  if(Kontext.getHeadword()) {
    Kontext.searchExamples();
  } else {
    $(".kontextbox .waiter").hide();
  }
};
Kontext.boxExamples=function(){
  var html="";
  html="<div class='kontextbox'>"
    html+="<form class='topbar' onsubmit='Kontext.searchExamples(); return false'>";
      if (kontext.concquery.length > 0) {
        html+="<input id='kontextsimple' type='radio' name='kontextsearchtype' value='kontextsimple'/>";
        html+="<label for='kontextsimple'>Simple search: </label>";
        html+="<input disabled name='val' class='textbox simple' value='"+Kontext.getHeadword()+"'/> ";
        html+="<input id='kontextcql' type='radio' name='kontextsearchtype' checked value='kontextcql'/>";
        html+="<label for='kontextcql'>CQL: </label>";
        html+="<input name='val' class='textbox cql focusme' value='"+Kontext.getCQL(kontext.concquery)+"'/> ";
      } else {
        html+="<input id='kontextsimple' type='radio' name='kontextsearchtype' checked value='kontextsimple'/>";
        html+="<label for='kontextsimple'>Simple search: </label>";
        html+="<input name='val' class='textbox simple focusme' value='"+Kontext.getHeadword()+"'/> ";
        html+="<input id='kontextcql' type='radio' name='kontextsearchtype' value='kontextcql'/>";
        html+="<label for='kontextcql'>CQL: </label>";
        html+="<input name='val' class='textbox cql' disabled/> ";
      }
      html+="<input type='submit' class='button kontext' value='&nbsp;'/>";
    html+="</form>";
    html+="<div class='waiter'></div>";
    html+="<div class='choices' style='display: none'></div>";
    html+="<div class='bottombar' style='display: none;'>";
      html+="<button class='prevnext' id='butKontextNext'>More »</button>";
      html+="<button class='prevnext' id='butKontextPrev'>«</button>";
      html+="<button class='insert' onclick='Kontext.insertExamples()'>Insert</button>";
    html+="</div>";
  html+="</div>";
  return html;
};
Kontext.toggleExample=function(inp){
  if($(inp).prop("checked")) $(inp.parentNode).addClass("selected"); else $(inp.parentNode).removeClass("selected");
};
Kontext.searchExamples=function(fromp){
  $("#butKontextPrev").hide();
  $("#butKontextNext").hide();
  $(".kontextbox .choices").hide();
  $(".kontextbox .bottombar").hide();
  $(".kontextbox .waiter").show();
  var query=$.trim($(".kontextbox input.textbox:enabled").val());
  var querytype=$("input[name=kontextsearchtype]:checked").val();
  if(query!="") {
    $.get("/"+dictId+"/kontext/conc/", {querytype: querytype, query: query, fromp: fromp}, function(json){
        $(".kontextbox .choices").html("");
        if(json.error && json.error=="Empty result"){
          $(".kontextbox .choices").html("<div class='error'>No results found.</div>");
          $(".kontextbox .waiter").hide();
          $(".kontextbox .choices").fadeIn();
        }
        else if(json.Lines) {
          if(json.pagination.prevPage) $("#butKontextPrev").show().on("click", function(){ Kontext.searchExamples(json.pagination.prevPage); $("div.kontextbox button.prevnext").off("click"); });
          if(json.pagination.nextPage) $("#butKontextNext").show().on("click", function(){ Kontext.searchExamples(json.pagination.nextPage); $("div.kontextbox button.prevnext").off("click"); });
          for(var iLine=0; iLine<json.Lines.length; iLine++){ var line=json.Lines[iLine];
            var left=""; for(var i=0; i<line.Left.length; i++) left+=line.Left[i].str; left=left.replace(/\<[^\<\>]+\>/g, "");
            var kwic=""; for(var i=0; i<line.Kwic.length; i++) kwic+=line.Kwic[i].str; kwic=kwic.replace(/<[^\<\>]+\>/g, "");
            var right=""; for(var i=0; i<line.Right.length; i++) right+=line.Right[i].str; right=right.replace(/<[^\<\>]+\>/g, "");
            var txt=left+"<b>"+kwic+"</b>"+right;
            txt=txt.replace("<b> ", " <b>");
            txt=txt.replace(" </b>", "</b> ");
            $(".kontextbox .choices").append("<label><input type='checkbox' onchange='Kontext.toggleExample(this)'/><span class='inside'>"+txt+"</span></label>");
            $(".kontextbox .waiter").hide();
            $(".kontextbox .choices").fadeIn();
            $(".kontextbox .bottombar").show();
          }
        } else {
          $(".kontextbox .choices").html("<div class='error'>There has been an error getting data from KonText.</div>");
          $(".kontextbox .waiter").hide();
          $(".kontextbox .choices").fadeIn();
        }
    });
  }
};
Kontext.getCQL=function(cql){
  var $xml=$($.parseXML(Xonomy.harvest()));
  var ret = cql.replace(/%\([^)]+\)/g, function (el) {
    return $xml.find(el.substring(2, el.length - 1)).html();
  })
  return ret;
};

Kontext.insertExamples=function(){
  $(".kontextbox div.choices label").each(function(){
    var $label=$(this);
    if($label.hasClass("selected")){
      var txt=$label.find("span.inside").html();
      if(kontext.markup) {
        txt=txt.replace("<b>", "<"+kontext.markup+">");
        txt=txt.replace("</b>", "</"+kontext.markup+">");
      } else {
        txt=txt.replace("<b>", "");
        txt=txt.replace("</b>", "");
      }
      var xml=kontext.template.replace("$text", txt);
      if(Kontext.htmlID) Xonomy.newElementChild(Kontext.htmlID, xml); else Xonomy.newElementLayby(xml);
    }
  });
};
