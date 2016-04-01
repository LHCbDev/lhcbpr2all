/**=========================================================
 * Directive: Responsive
 =========================================================*/
App.directive('beResponsive', function(){
	return {
		restrict: 'C', // used as a css class
		link: function(scope, element, attrs) {
			if(element.prop("tagName") == "TABLE")
				element.responsiveTable();
		}
	};
});
