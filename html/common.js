 
function extractHash() {
	var table  = {};
	var values = window.location.hash.substr(1);
	values = values.split("&");
	for (var i = 0; i < values.length; i++) {
		var tuple = values[i].split("=");
		var name  = tuple[0];
		var value = tuple.length > 1 ? tuple[1] : null;
		table[name] = value;
	}
	return table;
}

function formatDate(date) {
	d = new Date(date * 1000);
	return d.toTimeString().replace(/.*(\d{2}:\d{2}:\d{2}).*/, "$1");
}

var months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"];

function formatDay(date) {
	d = new Date(date * 1000);
	return d.getDate() + " " + months[d.getMonth()];
}

function formatDateTime(date) {
	if (date == null) return "";
	d = new Date(date * 1000);
	return d.getDate() + "." + (d.getMonth()+1) + " " + d.toTimeString().replace(/.*(\d{2}:\d{2}):\d{2}.*/, "$1");
}

function time() {
	return Math.round(new Date().getTime() / 1000);
}
