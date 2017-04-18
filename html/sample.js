
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
	.when("/connection/by/:field/:value", {
		templateUrl : "connectionlist.html",
		controller : "connectionlist"
	})
	.otherwise({
		templateUrl : "overview.html",
		controller : "overview"
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
	
	$http.get(api + "/connection/newest").then(function (httpResult) {
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
		$location.path("/connection/by/country/" + c);
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

app.controller('connectionlist', function($scope, $http, $routeParams) {

	$scope.connection = null;
	$scope.lines = [];
	
	$scope.formatDate = formatDateTime;
	$scope.nicenull = nicenull;
	$scope.short = short;
	$scope.encurl = encurl;
	$scope.decurl = decurl;
	
	var url = "";
	
	$scope.field = $routeParams.field;
	$scope.value = $routeParams.value;
	
	if ($routeParams.field == "country")
	{
		$scope.country     = $routeParams.value;
		$scope.countryname = COUNTRY_LIST[$scope.country];
		
		url = "/connection/by_country/" + $scope.country;
	}
	else if ($routeParams.field == "ip")
	{
		$scope.ip = $routeParams.value;
		
		url = "/connection/by_ip/" + $scope.ip;
	}
	
	$scope.older_than  = $routeParams.older_than ? $routeParams.older_than : null;
	var params         = "";
	
	if ($scope.older_than) params = "?older_than=" + $scope.older_than;
	
	$http.get(api + url + params).then(function (httpResult) {
		$scope.connections = httpResult.data;
		
		$scope.connections.map(function(connection) {
			connection.contryname = COUNTRY_LIST[connection.country];
			return connection;
		});
		
	});

});