
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
	.otherwise({
		templateUrl : "overview.html",
		controller : "overview"
	});
});

app.controller('overview', function($scope, $http, $routeParams) {

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
	
	$http.get(api + "/connection/newest").then(function (httpResult) {
		$scope.connections = httpResult.data;
	});
	
	$http.get(api + "/connection/statistics/per_country").then(function (httpResult) {
		httpResult.data.sort(function(a, b) { return b[0] - a[0] });
		
		$scope.country_stats_values = httpResult.data.map(function(x) {return x[0]});
		$scope.country_stats_labels = httpResult.data.map(function(x) {return COUNTRY_LIST[x[1]]});
	});
		
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
		console.log($scope.url);
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