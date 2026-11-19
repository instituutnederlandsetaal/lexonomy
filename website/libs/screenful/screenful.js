window.Screenful={
  status: function(str, style){
    if(window.parent!=window && window.parent.Screenful) window.parent.Screenful.status(str, style);
    else {
      if(style==="alert") {
        $("#statusbar .alertmessage .text").html(str);
        $("#statusbar .alertmessage").show();
      } else {
        if(style=="wait") str="<span class='wait'></span>"+str;
        if(style=="warn") str="<span class='warn'></span>"+str;
        $("#statusbar .statusmessage").html(str);
      }
    }
  },

  formatXml: function(xml) { //stolen from https://gist.github.com/sente/1083506
      var formatted = '';
      var reg = /(>)(<)(\/*)/g;
      xml = xml.replace(reg, '$1\r\n$2$3');
      var pad = 0;
      jQuery.each(xml.split('\r\n'), function(index, node) {
          var indent = 0;
          if (node.match( /.+<\/\w[^>]*>$/ )) {
              indent = 0;
          } else if (node.match( /^<\/\w/ )) {
              if (pad != 0) {
                  pad -= 1;
              }
          } else if (node.match( /^<\w[^>]*[^\/]>.*$/ )) {
              indent = 1;
          } else {
              indent = 0;
          }

          var padding = '';
          for (var i = 0; i < pad; i++) {
              padding += '  ';
          }

          formatted += padding + node + '\r\n';
          pad += indent;
      });

      return formatted;
  },
  cleanupXml: function(xml){
    return xml.trim().replace(/\>[\r\n]+\s*\</g, "><");
  },
  isWellFormedXml: function(xml){
    var doc=null;
    try{doc=$.parseXML(xml);} catch(e){}
    if(doc) return true;
    return false;
  },
};
