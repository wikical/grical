$(document).ready( function() {
    var datepicker = $( ".datePicker" );

    datepicker.datepicker({
        format: 'yyyy-mm-dd',
        autoclose: true,
        todayHighlight: true
    });
    $(window).on("resize", function () {
        datepicker.datepicker( 'hide' );
    });
});
