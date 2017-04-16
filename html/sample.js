
var app = angular.module('honey', ["ngRoute"]);

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
		template: "none"
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
	
	$scope.formatDate = formatDateTime;
	$scope.nicenull = nicenull;
	$scope.short = short;
	$scope.encurl = encurl;
	$scope.decurl = decurl;
	
	var id = $routeParams.id;
	$http.get(api + "/connection/" + id).then(function (httpResult) {
		$scope.connection = httpResult.data;
		console.log($scope.connection);
	});

});