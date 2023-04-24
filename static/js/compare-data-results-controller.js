/*
	Angular controller for all the Compare Objects results page
*/

var compareResultsApp = angular.module("compareResultsApp", ['ngRoute', 'ngResource']);

compareResultsApp.controller("CompareResultsController", function($scope, $http) 
{

	// On initation of controller
    $scope.init = function(job_id, object_id, fields)
    {
        // Job ID passed through from view
        $scope.job_id = job_id;

        // Object ID passed from the view
        $scope.object_id = object_id

        // The list of fields that were matched
        $scope.fields = fields.split(', ')

        // Array of unmatched records from org one
        $scope.org_one_records = [];

        // Execute AJAX call
    	$http(
        {
            method: 'GET',
            url: '/unmatched-rows/' + $scope.job_id + '/0/',
        }).
        success(function(data, status) 
        {
        	$scope.org_one_records = data;
        }).
        error(function(data, status) 
        {
            $('#orgone').html('<div role="alert" class="alert alert-danger">There was an error getting the unmatched rows for this org.');
        });

        // Array of unmatched records from org two
        $scope.org_two_records = [];

        // Execute AJAX call
    	$http(
        {
            method: 'GET',
            url: '/unmatched-rows/' + $scope.job_id + '/1/',
        }).
        success(function(data, status) 
        {
            $scope.org_two_records = data;
        }).
        error(function(data, status) 
        {
            $('#orgtwo').html('<div role="alert" class="alert alert-danger">There was an error getting the unmatched rows for this org.');
        });

        // Enable tooltips
		$('[data-toggle="tooltip"]').tooltip();
    }

    // When the compare button is checked.
    $scope.rerunJob = function()
    {
    	// Execute AJAX call
    	$http(
        {
            method: 'GET',
            url: '/compare-data/' + $scope.job_id + '/' + $scope.object_id + '/',
        }).
        success(function(data, status) 
        {
            // Redirect to the loading page
            window.location = data;
        }).
        error(function(data, status) 
        {
            // Return error in a modal
            updateModal(
                'Error Executing Data Compare',
                '<div class="alert alert-danger" role="alert">There was an error executing the data compare job.' + data + '</div>',
                true
            );

            // Close the modal
            $('#progressModal').modal();
        });

    }

});
