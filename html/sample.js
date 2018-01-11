var isMobile = false; //initiate as false
// device detection
if(/(android|bb\d+|meego).+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|ipad|iris|kindle|Android|Silk|lge |maemo|midp|mmp|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows (ce|phone)|xda|xiino/i.test(navigator.userAgent) 
    || /1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\-(n|u)|c55\/|capi|ccwa|cdm\-|cell|chtm|cldc|cmd\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\-s|devi|dica|dmob|do(c|p)o|ds(12|\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\-|_)|g1 u|g560|gene|gf\-5|g\-mo|go(\.w|od)|gr(ad|un)|haie|hcit|hd\-(m|p|t)|hei\-|hi(pt|ta)|hp( i|ip)|hs\-c|ht(c(\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\-(20|go|ma)|i230|iac( |\-|\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\/)|klon|kpt |kwc\-|kyo(c|k)|le(no|xi)|lg( g|\/(k|l|u)|50|54|\-[a-w])|libw|lynx|m1\-w|m3ga|m50\/|ma(te|ui|xo)|mc(01|21|ca)|m\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\-2|po(ck|rt|se)|prox|psio|pt\-g|qa\-a|qc(07|12|21|32|60|\-[2-7]|i\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\-|oo|p\-)|sdk\/|se(c(\-|0|1)|47|mc|nd|ri)|sgh\-|shar|sie(\-|m)|sk\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\-|v\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\-|tdg\-|tel(i|m)|tim\-|t\-mo|to(pl|sh)|ts(70|m\-|m3|m5)|tx\-9|up(\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\-|your|zeto|zte\-/i.test(navigator.userAgent.substr(0,4))) isMobile = true;

var app = angular.module('honey', ["ngRoute", "chart.js"]);

app.config(function($routeProvider) {
	$routeProvider
	.when("/samples", {
		templateUrl : "samples.html",
		controller : "samples"
	})
	.when("/sample/:sha256", {
		templateUrl : "sample.html",
		controller : "sample"
	})
	.when("/urls", {
		templateUrl : "urls.html",
		controller : "urls"
	})
	.when("/url/:url", {
		templateUrl : "url.html",
		controller : "url"
	})
	.when("/tag/:tag", {
		templateUrl : "tag.html",
		controller : "tag"
	})
	.when("/connection/:id", {
		templateUrl : "connection.html",
		controller : "connection"
	})
	.when("/asn/:asn", {
		templateUrl : "asn.html",
		controller : "asn"
	})
	.when("/networks", {
		templateUrl : "networks.html",
		controller : "networks"
	})
	.when("/connections", {
		templateUrl : "connectionlist.html",
		controller : "connectionlist"
	})
	.when("/tags", {
		templateUrl : "tags.html",
		controller : "tags"
	})
	.when("/admin", {
		templateUrl : "admin.html",
		controller : "admin"
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

    $scope.chart_options = {
        "animation": isMobile ? false : {}
    };

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

app.controller('samples', function($scope, $http, $routeParams) {

	$scope.samples = null;

	$scope.formatDate = formatDateTime;
	$scope.nicenull = nicenull;
	$scope.short = short;
	$scope.encurl = encurl;
	$scope.decurl = decurl;

	$http.get(api + "/sample/newest").then(function (httpResult) {
		$scope.samples = httpResult.data;
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

app.controller('urls', function($scope, $http, $routeParams) {

	$scope.url = null;

	$scope.formatDate = formatDateTime;
	$scope.nicenull = nicenull;
	$scope.short = short;
	$scope.encurl = encurl;
	$scope.decurl = decurl;

	$http.get(api + "/url/newest").then(function (httpResult) {
		$scope.urls = httpResult.data;
	});

});

app.controller('tags', function($scope, $http, $routeParams) {

	$scope.formatDate = formatDateTime;
	$scope.nicenull = nicenull;
	$scope.short = short;
	$scope.encurl = encurl;
	$scope.decurl = decurl;

	$http.get(api + "/tags").then(function (httpResult) {
		$scope.tags = httpResult.data;
	});

});

app.controller('networks', function($scope, $http, $routeParams) {

	$scope.formatDate = formatDateTime;
	$scope.nicenull = nicenull;
	$scope.short  = short;
	$scope.encurl = encurl;
	$scope.decurl = decurl;

	$http.get(api + "/networks").then(function (httpResult) {
		$scope.networks = httpResult.data;
		
		for (var i = 0; i < $scope.networks.length; i++)
		{
			var item = $scope.networks[i];
			item.order = item.urls.length + item.connections.length
				+ item.samples.length;
		}
	});
	
	$scope.filterNoSamples = function(network) {
		return network.samples.length > 0;
	};

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

app.controller('tag', function($scope, $http, $routeParams) {

	$scope.tag = null;

	$scope.formatDate = formatDateTime;
	$scope.nicenull = nicenull;
	$scope.short = short;
	$scope.encurl = encurl;
	$scope.decurl = decurl;

	var tag = $routeParams.tag;
	$http.get(api + "/tag/" + tag).then(function (httpResult) {
		$scope.tag         = httpResult.data;
        $scope.connections = $scope.tag.connections;
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
	$scope.displayoutput = true;

	var id = $routeParams.id;
	$http.get(api + "/connection/" + id).then(function (httpResult) {
		$scope.connection = httpResult.data;

		$scope.connection.countryname = COUNTRY_LIST[$scope.connection.country];
		
		var last_i = $scope.connection.stream.length - 1;
		$scope.connection.duration    = $scope.connection.stream[last_i].ts;

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
		"lacnic": "Latin America and Caribbean Network Information Centre",
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

app.controller('admin', function($scope, $http, $routeParams, $location) {

    $scope.loggedin = false;
    $scope.errormsg = null;

    $scope.username = null;
    $scope.password = null;

    $scope.new_username = null;
    $scope.new_password = null;

	$scope.login = function() {
        var auth = btoa($scope.username + ":" + $scope.password);
        $http.defaults.headers.common['Authorization'] = 'Basic ' + auth;
        $http.get(api + "/login").then(function (httpResult) {
            $scope.errormsg = "Logged in as " + $scope.username;
            $scope.loggedin = true;
        }, function (httpError) {
            $scope.errormsg = "Bad credentials";
        });
        $scope.password = null;
    };

	$scope.logout = function() {
        delete $http.defaults.headers.common['Authorization'];
        $scope.errormsg = null;
        $scope.loggedin = false;
        $scope.username = null;
        $scope.password = null;
    };

    $scope.addUser = function() {
        var newuser = {
            "username": $scope.new_username,
            "password": $scope.new_password
        };
        $http.put(api + "/user/" + newuser.username, newuser).then(function (httpResult) {
            $scope.errormsg     = "Created new user " + $scope.new_username;
            $scope.new_username = null;
            $scope.new_password = null;
        }, function (httpError) {
            $scope.errormsg     = "Error creating new user \"" + $scope.new_username + "\" :(";
            $scope.new_username = null;
            $scope.new_password = null;
        });
    };

});
