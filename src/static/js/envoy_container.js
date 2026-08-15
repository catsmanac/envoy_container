// Envoy data simulator functions and event processing

// tabbed view https://www.w3schools.com/howto/howto_js_tabs.asp
//
function openTab(evt, tabName) {
  // Declare all variables
  var i, tabcontent, tablinks;

  // Get all elements with class="tabcontent" and hide them
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }

  // Get all elements with class="tablinks" and remove the class "active"
  tablinks = document.getElementsByClassName("tablinks");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }

  // Show the current tab, and add an "active" class to the button that opened the tab
  document.getElementById(tabName).style.display = "block";
  evt.currentTarget.className += " active";
}

// copy element text to clipbord
//
function copyLog(id){
    const t = document.getElementById(id).innerText;
    navigator.clipboard.writeText(t);
}

// format date used for log lines
//
function logDate() {
    var timeStamp = Date.now();
    return new Date(timeStamp - (new Date().getTimezoneOffset() * 60 * 1000)).toISOString().slice(0,-1).split('T').join(' ')
};

// https://blog.centerkey.com/2013/05/javascript-colorized-pretty-print-json.html
const prettyPrintJson = {
   toHtml: (thing) => {
      const htmlEntities = (string) => {
         // Makes text displayable in browsers
         return string
            .replace(/&/g,   '&amp;')
            .replace(/\\"/g, '&bsol;&quot;')
            .replace(/</g,   '&lt;')
            .replace(/>/g,   '&gt;');
         };
      const replacer = (match, p1, p2, p3, p4) => {
         // Converts the four parenthesized capture groups into HTML
         const part =       { indent: p1, key: p2, value: p3, end: p4 };
         const key =        '<span class=json-key>';
         const val =        '<span class=json-value>';
         const bool =       '<span class=json-boolean>';
         const str =        '<span class=json-string>';
         const isBool =     ['true', 'false'].includes(part.value);
         const valSpan =    /^"/.test(part.value) ? str : isBool ? bool : val;
         const findName =   /"([\w]+)": |(.*): /;
         const indentHtml = part.indent || '';
         const keyName =    part.key && part.key.replace(findName, '$1$2');
         const keyHtml =    part.key ? key + keyName + '</span>: ' : '';
         const valueHtml =  part.value ? valSpan + part.value + '</span>' : '';
         const endHtml =    part.end || '';
         return indentHtml + keyHtml + valueHtml + endHtml;
         };
      const jsonLine = /^( *)("[^"]+": )?("[^"]*"|[\w.+-]*)?([{}[\],]*)?$/mg;
      return htmlEntities(JSON.stringify(thing, null, 3))
         .replace(jsonLine, replacer);
      }
   };

// include html
// https://www.w3schools.com/howto/howto_html_include.asp
// 
function includeHTML() {
  var z, i, elmnt, file, xhttp;
  /* Loop through a collection of all HTML elements: */
  z = document.getElementsByTagName("*");
  for (i = 0; i < z.length; i++) {
    elmnt = z[i];
    /*search for elements with a certain atrribute:*/
    file = elmnt.getAttribute("w3-include-html");
    console.log(file)
    if (file) {
      /* Make an HTTP request using the attribute value as the file name: */
      xhttp = new XMLHttpRequest();
      xhttp.onreadystatechange = function() {
        if (this.readyState == 4) {
          if (this.status == 200) {elmnt.innerHTML = this.responseText;}
          if (this.status == 404) {elmnt.innerHTML = "Page not found.";}
          /* Remove the attribute, and call this function once more: */
          elmnt.removeAttribute("w3-include-html");
          includeHTML();
        }
      }
      xhttp.open("GET", file, true);
      xhttp.send();
      /* Exit the function: */
      return;
    }
  }
}

// connect to socketio and send/receive messages
//
$(document).ready(function(){
    var socket = io();

    // Add line to logging box on index page
    //
    socket.on('logger', function(msg) {
        let timestamp = logDate()
        var e = document.getElementById('log');
        e.innerHTML += (logDate() + ' ' + msg.data + ' <br>')
        e.scrollTop = e.scrollHeight; // Auto-scroll to bottom
    });

    // update html elements
    //
    // in python:  emit('updateElement',{'id': "value", .. , .. }
    // 
    socket.on('updateElement', function(msg) {
        let timestamp = logDate()
        for (var i in msg) {
            var v = document.getElementById(i)
            if (v) v.innerHTML = msg[i];
        }
    });

    // update XML elements (innertext)
    //
    socket.on('updateXML', function(msg) {
        let timestamp = logDate()
        for (var i in msg) {
            var v = document.getElementById(i)
            if (v) v.innerText = msg[i];
        }
    });

    // update pretty layout json elements
    //
    socket.on('updateJSON', function(msg) {
        let timestamp = logDate()
        socket.emit('logger', msg);
        for (var i in msg) {
            var v = document.getElementById(i)
            socket.emit('logger', {data: v + ' ' + msg[i]});
            if (v) v.innerHTML = prettyPrintJson.toHtml(msg[i]);
            // JSON.stringify(msg[i], undefined, 2);
        }
    });

    // signal (server/python) to load new sim
    //
    $('#btnchangesim').on("click", function(event) {
        var v = $('#select_sim').find(":selected").val();
        var id = this.id
        socket.emit(id, {data: v});
    });

    // signal (server/python) to remember fixture in .env
    //
    $('#btnremembersim').on("click", function(event) {
        var v = $('#select_sim').find(":selected").val();
        var id = this.id
        socket.emit(id, {data: v});
    });

    // signal (server/python) to reload cache list
    //
    $('#btncacherefresh').on("click", function(event) {
        var v = document.getElementById('cachename')
        var id = this.id
        socket.emit(id, {data:  v.textContent || v.innerText });
    });
    

    // signal (server/python) to reload fixture list
    //
    $('#btnfixturesrefresh').on("click", function(event) {
        var v = document.getElementById('fixturename')
        var id = this.id
        socket.emit(id, {data: v.textContent || v.innerText });
    });

    // signal (server/python) to toggle states
    //
    $('.togglebool').on("click", function(event) {
        var id = this.id
        socket.emit("togglebool", {data: id});
    });

    // signal (server/python) to toggle states
    //
    $('.sendid').on("click", function(event) {
        socket.emit(this.id, {data: ""});
    });

    // Add log message on client connect
    //
    socket.on('connect', function() {
        socket.emit('logger');
    });

    // handle clicked entry in fixture file list
    // signal (server/python) to update our fixture file content viewer
    // 
    $('#fixturefiles').on('click',function(event){
        socket.emit('showfixturefile', {data: event.target.id});
    });

    // handle clicked entry in cache file list
    // signal (server/python) to update our cache file content viewer
    // 
    $('#cachefiles').on('click',function(event){
        socket.emit('showcachefile', {data: event.target.id});
    });

});