// Process.js: Handles linkage between web frontend and server backend

$(document).ready(function() {
    function showMentions() {
        var elt=this.parentElement.querySelector(".mentions");
        elt.style.display=(elt.style.display=="block") ? "none" : "block";
    }

    function formatMentionsInto(sources, keyword, list) {
        while (list.firstChild) list.removeChild(list.firstChild);

        var mentions=sources[keyword];

        var fragment=document.createDocumentFragment();
        for (var i=0; i<mentions.length; ++i) {
            var item=document.createElement("li")
            item.appendChild(document.createTextNode("Comment "));

            var l=document.createElement("a");
            l.target="_blank";
            l.href="https://reddit.com"+mentions[i][1];
            l.appendChild(document.createTextNode(mentions[i][0]));
            item.appendChild(l);

            fragment.appendChild(item);
        }

        list.appendChild(fragment.cloneNode(true));
    }


    function formatResultsInto(keywords, list, sources) {
        while (list.firstChild) list.removeChild(list.firstChild);

        var fragment=document.createDocumentFragment();
        for (var i=0; i<keywords.length; ++i) {
            var item=document.createElement("li")
            item.appendChild(document.createTextNode(keywords[i][2]));
            item.appendChild(document.createElement("br"));

            var l=document.createElement("span");
            l.className="mentionsTrigger";
            l.appendChild(document.createTextNode(keywords[i][3]+" mentions,"));
            item.appendChild(l);

            item.appendChild(document.createTextNode(" including at comment "));

            l=document.createElement("a");
            l.href="https://reddit.com"+keywords[i][1];
            l.target="_blank";
            l.appendChild(document.createTextNode(keywords[i][0]));
            item.appendChild(l);

            l=document.createElement("div");
            l.className="mentions";
            l.style.display="none";
            var e=document.createElement("h5");
            e.appendChild(document.createTextNode("Mentions for \""+keywords[i][2]+"\":"));
            l.appendChild(e);

            e=document.createElement("ul");
            formatMentionsInto(sources, keywords[i][2], e);
            l.appendChild(e);
            item.append(l);

            fragment.appendChild(item);
        }

        list.appendChild(fragment.cloneNode(true));

        // Make sure we don't add two handlers by repeated binding
        $(".mentionsTrigger").unbind("click").click(showMentions);
    }

    var cancel=undefined;
    var lastRequest="";
    $("#trigger").click(function() {
      // Server request
      var target={};
      target.target=document.getElementById("target").value;
      if (document.getElementById("unlimited").checked) {
          target.limit=0;
          target.comments2=false;
      }
      else {
          target.limit=document.getElementById("slider").value;
          target.comments2=true;
      }

      var thisRequest=lastRequest=target;

      var loader=document.getElementById("loading");

      if (cancel!==undefined) {
          clearInterval(cancel);
          loader.innerHTML="&nbsp;";
          loader.style.display="none";
      }

      document.getElementById("error").style.display="none";
      document.getElementById("results").style.display="none";

      $.ajax({
          type: "POST",
          url: "/process",
          crossDomain: true,
          data: target,
          success: function (processed) {
              if (thisRequest!==lastRequest) return;

              // End loading animation
              clearInterval(cancel);
              loader.innerHTML="&nbsp;";
              loader.style.display="none";
              cancel=undefined;

              try {
                  document.getElementById("relatedCount").innerHTML=processed.related.length;
                  document.getElementById("unrelatedCount").innerHTML=processed.unrelated.length;
                  formatResultsInto(processed.related, document.getElementById("related"), processed.sources);
                  formatResultsInto(processed.unrelated, document.getElementById("unrelated"), processed.sources);

                  document.getElementById("results").style.display="block";
              }
              catch (e) {
                  console.log("Encountered error: "+e+":\n"+e.stack);

                  document.getElementById("results").style.display="none";
                  document.getElementById("error").style.display="block";
              }
          },
          error: function(xhr, str, exc) {
              // End loading animation
              clearInterval(cancel);
              loader.innerHTML="&nbsp;";
              loader.style.display="none";
              cancel=undefined;

              if (exc) {
                  console.log("Error: "+str+"\n"+exc);
              }
              else {
                  console.log("Error: "+str);
              }
              document.getElementById("results").style.display="none";
              document.getElementById("error").style.display="block";
          }
      });

      loader.style.display="block";
      var n=0;
      cancel=setInterval(function() {
          if (n>=3) {
              n=0;
              loader.innerHTML="&nbsp;";
          }
          else {
              ++n;
              loader.innerHTML+=".";
          }
      }, 1000);
   });

   function updateUnits() {
      var units=document.getElementById("sliderUnit");
      var value=document.getElementById("slider").value;
      var comments2=true;

      if (comments2) {
          if (value==1) {
              units.innerHTML="replacement";
          }
          else {
              units.innerHTML="replacements";
          }
      }
      else {
          if (value==0) {
              units.innerHTML="";
          }
          else if (value==1) {
              units.innerHTML="comment";
          }
          else {
              units.innerHTML="comments";
          }
      }
   }

   function updateCount() {
      var label=document.getElementById("sliderValue");
      var value=this.value;
      var comments2=true;

      if (value==0) {
          if (comments2){
             label.innerHTML="No";
          }
          else {
            label.innerHTML="None";
          }
      }
      else {
          label.innerHTML=value.toString();
      }

      updateUnits();
   }

   $("#slider").change(updateCount).on("input", updateCount);

   $("#slider").trigger("change");

   $("#comments2").change(function() {
      var slider=document.getElementById("slider");
      if (this.checked) {
          slider.value=Math.floor((slider.value/slider.max)*100);
          slider.max=100;
      }
      else {
          var value=Math.floor((slider.value/slider.max)*1000);
          slider.max=1000;
          slider.value=value;
      }
      $("#slider").trigger("change");
   });

   // Now, the handler for pressing enter in the text field
   $("#target").keyup(function(e) {
       if (e.keyCode==13) {
           $("#trigger").click();
       }
   });

   $("#comments2").trigger("change");
});
