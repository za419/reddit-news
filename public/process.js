// Process.js: Handles linkage between web frontend and server backend

$(document).ready(function() {
   $("#trigger").click(function() {
      // Server request
      var target={};
      target.target=document.getElementById("target").value;
      var cancel;

      $.ajax({
          type: "POST",
          url: "/process",
          crossDomain: true,
          data: target,
          success: function (processed) {
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
              if (exc) {
                  console.log("Error: "+str+"\n"+exc);
              }
              else {
                  console.log("Error: "+str);
              }
              document.getElementById("results").style.display="none";
          }
      });

      var loader=document.getElementById("loading");
      loader.style.display="block";
      var n=0;
      cancel=setInterval(function() {
          if (n>=3) {
              n=0;
              loader.innerHTML="";
          }
          else {
              ++n;
              loader.innerHTML+=".";
          }
      }, 1000);
   });
});
