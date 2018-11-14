// Process.js: Handles linkage between web frontend and server backend

$(document).ready(function() {
   $("#trigger").click(function() {
      var target={};
      target.target=document.getElementById("target").value;

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
      })
   });
});
