<html>
<head>
  <title>Canvas Demo</title>
  %include header description='', keywords='', author=''

  <script type="application/javascript">  
    //https://developer.mozilla.org/en/Canvas_tutorial/Basic_usage
    function draw(){  
      var canvas = document.getElementById('tutorial');  
      if (canvas.getContext){  
        var ctx = canvas.getContext('2d');  
   
        ctx.fillStyle = "rgb(200,0,0)";  
        ctx.fillRect (10, 10, 55, 50);  
  
        ctx.fillStyle = "rgba(0, 0, 200, 0.5)";  
        ctx.fillRect (30, 30, 55, 50);  
      }  
    }  

  </script>

</head>
<body onload="draw();">
  <h1>Canvas Demo</h1>

  <canvas id="tutorial" width="150" height="150">fallback content</canvas>

  <hr />

  <a href="https://developer.mozilla.org/en/Canvas_tutorial/Basic_usage">https://developer.mozilla.org/en/Canvas_tutorial/Basic_usage</a>


</body>
</html>
