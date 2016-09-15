$(document).ready( function() {
    var options = {
      dateFormat: 'yy-mm-dd',
      changeYear: true,
      constrainInput: false
    };
    // http://docs.jquery.com/UI/Datepicker    
    $( ".datePicker" ).datepicker( options );
});
