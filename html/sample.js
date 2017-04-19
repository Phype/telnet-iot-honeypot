
var app = angular.module('honey', ["ngRoute", "chart.js"]);

app.config(function($routeProvider) {
	$routeProvider
	.when("/sample/:sha256", {
		templateUrl : "sample.html",
		controller : "sample"
	})
	.when("/url/:url", {
		templateUrl : "url.html",
		controller : "url"
	})
	.when("/connection/:id", {
		templateUrl : "connection.html",
		controller : "connection"
	})
	.when("/asn/:asn", {
		templateUrl : "asn.html",
		controller : "asn"
	})
	.when("/connections", {
		templateUrl : "connectionlist.html",
		controller : "connectionlist"
	})
	.when("/", {
		templateUrl : "overview.html",
		controller : "overview"
	})
	.otherwise({
		template: '<h1>Error</h1>View not found.<br><a href="#/">Go to index</a>'
	});
});

app.controller('overview', function($scope, $http, $routeParams, $location) {

	$scope.urls = null;
	$scope.samples = null;
	$scope.connections = null;
	
	$scope.formatDate = formatDateTime;
	$scope.nicenull = nicenull;
	$scope.short = short;
	$scope.encurl = encurl;
	$scope.decurl = decurl;
	
	$http.get(api + "/url/newest").then(function (httpResult) {
		$scope.urls = httpResult.data;
	});
	
	$http.get(api + "/sample/newest").then(function (httpResult) {
		$scope.samples = httpResult.data;
	});
	
	$http.get(api + "/connections").then(function (httpResult) {
		$scope.connections = httpResult.data;
	});
	
	$http.get(api + "/connection/statistics/per_country").then(function (httpResult) {
		httpResult.data.sort(function(a, b) { return b[0] - a[0] });
		
		$scope.country_stats_values = httpResult.data.map(function(x) {return x[0]});
		$scope.country_stats_labels = httpResult.data.map(function(x) {return COUNTRY_LIST[x[1]]});
		$scope.country_stats_data   = httpResult.data.map(function(x) {return x[1]});
	});
	
	$scope.clickchart_countries = function(a,b,c,d,e) {
		var c = $scope.country_stats_data[c._index];
		$location.path("/connections").search({country: c});
		$scope.$apply()
	};
		
});

app.controller('sample', function($scope, $http, $routeParams) {

	$scope.sample = null;
	
	$scope.formatDate = formatDateTime;
	$scope.nicenull = nicenull;
	$scope.short = short;
	$scope.encurl = encurl;
	$scope.decurl = decurl;
	
	$scope.short = function (str) {
		if (str)
			return str.substring(0, 16) + "...";
		else
			return "None";
	};
	
	var sha256 = $routeParams.sha256;
	$http.get(api + "/sample/" + sha256).then(function (httpResult) {
		$scope.sample = httpResult.data;
	});

});

app.controller('url', function($scope, $http, $routeParams) {

	$scope.url = null;
	
	$scope.formatDate = formatDateTime;
	$scope.nicenull = nicenull;
	$scope.short = short;
	$scope.encurl = encurl;
	$scope.decurl = decurl;
	
	var url = $routeParams.url;
	$http.get(api + "/url/" + url).then(function (httpResult) {
		$scope.url = httpResult.data;
		$scope.url.countryname = COUNTRY_LIST[$scope.url.country];
	});

});

app.controller('connection', function($scope, $http, $routeParams) {

	$scope.connection = null;
	$scope.lines = [];
	
	$scope.formatDate = formatDateTime;
	$scope.nicenull = nicenull;
	$scope.short = short;
	$scope.encurl = encurl;
	$scope.decurl = decurl;
	
	var id = $routeParams.id;
	$http.get(api + "/connection/" + id).then(function (httpResult) {
		$scope.connection = httpResult.data;
	
		$scope.connection.countryname = COUNTRY_LIST[$scope.connection.country];
		
		var lines = $scope.connection.text_combined.split("\n");
		var newl  = [];
		for (var i = 0; i < lines.length; i++)
		{
			newl.push({
				text: lines[i],
				is_input: lines[i].startsWith(" #")
			});
		}
		
		$scope.lines = newl;
		
	});

});

app.controller('connectionlist', function($scope, $http, $routeParams, $location) {

	$scope.connection = null;
	$scope.lines = [];
	
	$scope.formatDate = formatDateTime;
	$scope.nicenull = nicenull;
	$scope.short = short;
	$scope.encurl = encurl;
	$scope.decurl = decurl;
	$scope.COUNTRY_LIST = COUNTRY_LIST;
	
	$scope.filter = $routeParams;
	
	var url = api + "/connections?";
	
	for (key in $routeParams)
	{
		url = url + key + "=" + $routeParams[key] + "&";
	}
	
	$http.get(url).then(function (httpResult) {
		$scope.connections = httpResult.data;
		
		$scope.connections.map(function(connection) {
			connection.contryname = COUNTRY_LIST[connection.country];
			return connection;
		});
		
	});
	
	$scope.nextpage = function() {
		var filter = $scope.filter;
		
		filter['older_than'] = $scope.connections[$scope.connections.length - 1].date;
		
		$location.path("/connections").search(filter);
		$scope.$apply();
	};

});

app.controller('asn', function($scope, $http, $routeParams, $location) {

	$scope.connection = null;
	$scope.lines = [];
	
	$scope.formatDate = formatDateTime;
	$scope.nicenull = nicenull;
	$scope.short = short;
	$scope.encurl = encurl;
	$scope.decurl = decurl;
	$scope.COUNTRY_LIST = COUNTRY_LIST;
	$scope.REGISTRIES = {
		"arin": "American Registry for Internet Numbers",
		"ripencc": "RIPE Network Coordination Centre",
		"latnic": "Latin America and Caribbean Network Information Centre",
		"afrinic": "African Network Information Centre",
		"apnic": "Asia-Pacific Network Information Centre"
	};
	
	var asn = $routeParams.asn;
	$scope.filter = { "asn_id" : asn};
	
	$http.get(api + "/asn/" + asn).then(function (httpResult) {
		$scope.asn = httpResult.data;
		$scope.asn.countryname = COUNTRY_LIST[$scope.asn.country];
		
		$scope.connections = $scope.asn.connections.sort(function(x, y) {return y.date - x.date} ).slice(0,8);
		$scope.urls = $scope.asn.urls.sort(function(x, y) {return y.date - x.date} ).slice(0,8);
	});

});