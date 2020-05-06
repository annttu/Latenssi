function update_images()
{
    var images = [].slice.call(document.getElementsByTagName("img"));
    for (idx in images) {
        var img = images[idx];
        var url = img.src
        if (url.indexOf('dummy=') != -1) url = url.substring(0, url.indexOf('dummy=') - 1)
        if (url.indexOf('?') != -1) url += "&dummy=";
        else url += "?dummy=";
        url += new Date().getTime();
        img.src = url;
    }
}

var current_time = {};
var step = 3600;

function goback(img) {
   imgid = "img-" + img;
   if (!(imgid in current_time)) {
       var seconds = Math.floor(new Date().getTime() / 1000);
       current_time[imgid] = seconds;
   }
   current_time[imgid] -= step;
   goImage(imgid, current_time[imgid]);
}

function guessInterval(stepname) {
    if (stepname == "hour") return 3600;
    if (stepname.includes("hour")) {
       hours = parseInt(stepname.substr(0, stepname.length-4))
       return hours * 3600;
    }
    if (stepname == "day") return 24*3600;
    if (stepname == "week") return 7*24*3600;
    if (stepname == "month") return 30*24*3600;
    if (stepname == "year") return 365*24*3600;
    return 3600;
}

function goImage(imgid, end) {
   var start = end - step;
   imgElement = document.getElementById(imgid);
   var currentURL = new URL(imgElement.src);
   currentURL.search = "?start=" + start + "&end=" + end;
   imgElement.src = currentURL.href;
}
function goforward(img) {
   imgid = "img-" + img;
   if (!(imgid in current_time)) {

   }
   current_time[imgid] += step;
   goImage(imgid, current_time[imgid]);
}

function latenssi() {
    setInterval(update_images, 300000);
    x = document.location.pathname.split("/");
    step = guessInterval(x[x.length-1]);
}
