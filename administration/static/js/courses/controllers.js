(function(angular){
    'use strict';

    var app = angular.module('courses');

    app.controller('CoursesAdminController', [
        '$scope', '$uibModal', '$window', 'Course', 'Lesson', 'FormUpload',
        function ($scope, $uibModal, $window, Course, Lesson, FormUpload) {

            $scope.courseList = [];
            $scope.ordering = 'start_date';
            $scope.reverse = false;
            $scope.filters = {
                all: false,
                published : true,
                draft : true,
                textsearch: '',
                check : function(course){
                    var f = $scope.filters;
                    var search = f.textsearch.toLowerCase();
                    var target = course.name.toLowerCase();

                    return (
                        f.all || f[course.status]
                    ) && (
                        !search || target.match(search)
                    );
                }
            };

            $scope.loadLessons = function(course) {
                if(!course.lessons) {
                    Lesson.query({'course__id': course.id}).$promise
                        .then(function(lessons){
                            course.lessons = lessons;
                        });
                }
            };

            Course.query({'role': 'coordinator'}, function(list){
                $scope.courseList = list;
            });

            function send_course_file(course_import_file, force) {
                var msg = '';

                $scope.fu = new FormUpload();
                $scope.fu.addField('course-import-file', course_import_file);

                if (force)
                    $scope.fu.addField('force', true);

                $scope.fu.sendTo('/admin/course/import/')
                    .then(function(response) {
                        if (response.data.error) {
                            if (response.data.error == 'course_started') {
                                msg = 'O curso que você está tentando importar já começou. Só é possivel importar um curso já existente quando ele ainda não começou.';
                                alert(msg);
                                return;
                            }
                            else if (response.data.error == 'invalid_file') {
                                msg = 'Arquivo de importação inválido.';
                                alert(msg);
                                return;
                            }
                            else if (response.data.error == 'course_exists') {
                                msg = 'O curso que você está tentando importar já existe. Você pode importar o curso mesmo assim, mas TODAS AS INFORMAÇÕES RELATIVAS AOS CAPÍTULOS COMPLETOS PELOS USUÁRIOS SERÃO PERDIDAS. Importar curso mesmo assim?';
                                if (confirm(msg)){
                                    send_course_file(course_import_file, true);
                                }
                            }
                        } else {
                            $window.location.href = response.data.new_course_url;
                        }
                    }, function(response){
                        msg = 'Erro ao importar arquivo de curso!';
                        alert(msg);
                        return;
                    });
            }

            $scope.import_course_modal = function () {
                var modalInstance = $uibModal.open({
                    templateUrl: 'import_course_modal.html',
                    controller: ['$scope', '$uibModalInstance', ImportCourseModalInstanceCtrl]
                });
                modalInstance.result.then(function (course_import_file) {
                    send_course_file(course_import_file);
                });
            };
            var ImportCourseModalInstanceCtrl = function ($scope, $uibModalInstance) {
                $scope.cancel = function () {
                    $uibModalInstance.dismiss();
                };

                $scope.import_course = function () {
                    $uibModalInstance.close($scope.course_import_file);

                };
            };
        }
    ]);

    /**
     *  MOVED TO my-courses
     *
    **/
    app.controller('CourseListByUserRoleController', [
        '$scope', '$window', '$uibModal', 'Lesson', 'CourseProfessor', 'Class',
        function ($scope, $window, $uibModal, Lesson, CourseProfessor, Class) {
            var current_user_id = parseInt($window.user_id, 10);

            $scope.loadLessons = function(course) {
                if(!course.lessons) {
                    Lesson.query({'course__id': course.id}).$promise
                        .then(function(lessons){
                            course.lessons = lessons;
                        });
                }
            };

            $scope.courses_user_assist = CourseProfessor.query({'user': current_user_id,
                          'role': 'assistant'});

            $scope.courses_user_coordinate = CourseProfessor.query({'user': current_user_id,
                          'role': 'coordinator'});

            $scope.open_professor_modal = function(course_professor) {
                var modalInstance = $uibModal.open({
                       templateUrl: 'create_class_modal.html',
                       controller: CreateClassModalInstanceCtrl,
                       resolve: {
                           course_professor: function () {
                               return course_professor;
                           }
                       }
                });
                modalInstance.result.then(function (course_professor) {
                });
            };

            var CreateClassModalInstanceCtrl = function($scope, $uibModalInstance, course_professor) {
                $scope.course = course_professor.course;

                $scope.cancel = function () {
                    $uibModalInstance.dismiss();
                };
            };
        }
    ]);
})(window.angular);
