
var fakenames = ["Boar","Stallion","Yak","Beaver","Salamander","Eagle Owl","Impala","Elephant","Chameleon","Argali","Lemur","Addax","Colt","Whale","Dormouse","Budgerigar","Dugong","Squirrel","Okapi","Burro","Fish","Crocodile","Finch","Bison","Gazelle","Basilisk","Puma","Rooster","Moose","Musk Deer","Thorny Devil","Gopher","Gnu","Panther","Porpoise","Lamb","Parakeet","Marmoset","Coati","Alligator","Elk","Antelope","Kitten","Capybara","Mule","Mouse","Civet","Zebu","Horse","Bald Eagle","Raccoon","Pronghorn","Parrot","Llama","Tapir","Duckbill Platypus","Cow","Ewe","Bighorn","Hedgehog","Crow","Mustang","Panda","Otter","Mare","Goat","Dingo","Hog","Mongoose","Guanaco","Walrus","Springbok","Dog","Kangaroo","Badger","Fawn","Octopus","Buffalo","Doe","Camel","Shrew","Lovebird","Gemsbok","Mink","Lynx","Wolverine","Fox","Gorilla","Silver Fox","Wolf","Ground Hog","Meerkat","Pony","Highland Cow","Mynah Bird","Giraffe","Cougar","Eland","Ferret","Rhinoceros"];

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

function nicenull (str, el) {
	if (str == null || str == "")
		return el;
	else
		return str;
}

function short (str, l) {
	if (str)
		return str.substring(0, l) + "...";
	else
		return "None";
}

function encurl(url) {
	return btoa(url);
}

function decurl(url) {
	return atob(url);
}
