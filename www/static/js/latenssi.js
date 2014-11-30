
function update_images()
{
	console.log("Updating images");
	$("img").each(function(index, value){
		var url = $(value).attr("src");
		if (url.indexOf('dummy=') != -1) url = url.substring(0, url.indexOf('dummy=') - 1)
		if (url.indexOf('?') != -1) url += "&dummy=";
		else url += "?dummy=";
		url += new Date().getTime();
		$(value).attr("src", url);
	})
}

$(document).ready(function(){
	setInterval(update_images, 300000);
});
