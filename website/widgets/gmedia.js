window.Gmedia = {};
Gmedia.addVoice=function(entry) {
  if (gapi.voicekey && gapi.voicekey != '' && gapi.voicelang != '') {
    if (entry) {
      var $xml = $($.parseXML(entry.content));
    } else {
      var $xml = $($.parseXML(Xonomy.harvest()));
    }
    var headword = $xml.find(titling.headword).html();
    if (headword != '') {
      $('#viewer').append('<div id="voicetts"><audio controls src="https://api.voicerss.org/?key='+gapi.voicekey+'&hl='+gapi.voicelang+'&src='+headword+'"/></div>');
      $('#editor').append('<div id="voicetts"><audio controls src="https://api.voicerss.org/?key='+gapi.voicekey+'&hl='+gapi.voicelang+'&src='+headword+'"/></div>');
    }
  }
}

Gmedia.addVoicePublic=function(entry, gapi, titling) {
   var $xml = $($.parseXML(entry.content));
   var headword = $xml.find(titling.headword).html();
   if (headword != "" && gapi.voicekey && gapi.voicekey != '' && gapi.voicelang != '') {
      $('#viewer div:first span:first').after('<span class="voicetts"><audio id="voiceplayer" src="https://api.voicerss.org/?key='+gapi.voicekey+'&hl='+gapi.voicelang+'&src='+headword+'"/><span class="voicetts-icon"><img src="./furniture/speaker.png" onclick="document.getElementById(\'voiceplayer\').play()"></span></span>');
   }
}
