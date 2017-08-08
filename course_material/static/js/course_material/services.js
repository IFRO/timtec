
(function (angular) {
    'use strict';

    /* Services */

    angular.module('courseMaterial.services', ['ngRoute', 'ngResource']).
        factory('CourseMaterial', function($resource){
            return $resource('/api/course_material/:course/', {}, {
                update: {method: 'PUT'}
            });
        }).
        factory('CourseMaterialFile', function($resource){
            return $resource('/api/course_material_file/:id/', {}, {
                update: {method: 'PUT'}
            });
        }).
        factory('Course', function($resource){
            return $resource('/api/course/:id');
        });
})(angular);
