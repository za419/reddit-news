// Process.js: Handles linkage between web frontend and server backend

$(document).ready(function() {
   var cancel=undefined;
   var lastRequest="";
   $("#trigger").click(function() {
      // Server request
      var target={};
      target.target=document.getElementById("target").value;
      target.limit=document.getElementById("slider").value;
      target.comments2=document.getElementById("comments2").checked;

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

              document.getElementById("article").innerHTML=processed.text;

              var list=document.getElementById("comments");
              var fragment=document.createDocumentFragment();
              for (var i=0; i<processed.comments.length; ++i) {
                  var item=document.createElement("li")
                  item.appendChild(document.createTextNode("Comment "));

                  var l=document.createElement("a");
                  l.href="https://reddit.com"+processed.comments[i][1];
                  l.appendChild(document.createTextNode(processed.comments[i][0]));
                  item.appendChild(l);

                  item.appendChild(document.createElement("br"));
                  item.appendChild(document.createTextNode(processed.comments[i][2]));

                  fragment.appendChild(item);
              }

              list.appendChild(fragment.cloneNode(true));

              document.getElementById("count").innerHTML=processed.comments.length.toString();
              document.getElementById("results").style.display="block";
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
      var comments2=document.getElementById("comments2").checked;

      if (value==0) {
          units.innerHTML="";
      }
      else if (value==1) {
          if (comments2) {
              units.innerHTML="replacement";
          }
          else {
              units.innerHTML="comment";
          }
      }
      else {
          if (comments2) {
              units.innerHTML="replacements";
          }
          else {
              units.innerHTML="comments";
          }
      }
   }

   function updateCount() {
      var label=document.getElementById("sliderValue");
      var value=this.value;

      if (value==0) {
          label.innerHTML="None";
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
});
