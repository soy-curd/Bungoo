function change(id,src,rR,rG,rB, A) {
    var canvas = document.getElementById(id),
        picWidth = $('#canvsid').width(),
        picHeight = $('#canvsid').height(),
        picLength = picWidth * picHeight,
        mg = new Image();
    if (canvas.getContext) {
        ctx = canvas.getContext("2d");
        mg.onload = function() {
            var imgH = mg.height,
                imgW = mg.width,
                imgHhalf = mg.height/2,
                imgWhalf = mg.width/2,
                imgx = imgWhalf - picWidth/2,
                imgy = imgHhalf - picHeight/2;
            ctx.drawImage(mg,imgx,imgy,picWidth,picHeight,0,0,picWidth,picHeight);
            mg = ctx.getImageData(0, 0, picWidth, picHeight);
            for (var i = 0; i < picLength * 4; i += 4) {
                var myRed = mg.data[i];
                var myGreen = mg.data[i + 1];
                var myBlue = mg.data[i + 2];
                var myA = mg.data[i + 3];

                mg.data[i] = myRed + rR;
                mg.data[i + 1] = myGreen + rG;
                mg.data[i + 2] = myBlue + rB;
                mg.data[i + 3] = myA + A;
            }
            ctx.putImageData(mg, 0, 0);
        }
        mg.src = src;
    }
}

function draw(id, image) {
    var canvas = document.getElementById('canvsid');
    if ( ! canvas || ! canvas.getContext ) { return false; }
    var ctx = canvas.getContext('2d');
    /* Imageオブジェクトを生成 */
    var img = new Image();
    img.src = image + "?" + new Date().getTime();
    /* 画像が読み込まれるのを待ってから処理を続行 */
    img.onload = function() {
        //ctx.drawImage(img, 0, 0);
        change(id, image, 0, 0, 0, -100);
    }
}

onload = function() {
    onadraw('onaho', '/static/img/tenga.jpg')
}

function onadraw(id, src) {
    var canvas = document.getElementById(id);
    if ( ! canvas || ! canvas.getContext ) { return false; }
    var ctx = canvas.getContext('2d');
    /* Imageオブジェクトを生成 */
    var img = new Image();
    img.src = src + '?' + new Date().getTime();
    img.onload = function() {
        ctx.drawImage(img, 0, 0);
    }
}
