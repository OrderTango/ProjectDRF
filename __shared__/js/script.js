$(document).ready(function() {
    /* Left Sidebar Script Start */
    $('.btn-expand-collapse-left').click(function(e) {
        if ($('.navbar-primary').hasClass('collapsed') == false) {
            $('.navbar-primary').toggleClass('collapsed');
            $('.overFlowLeft').hide();
            $('#profileInfoDiv').css('margin','40% 0% 65% 0%');
            $('#logoCompany').css('margin','10px 0px 10px 0px');
            $('#bodyContent').css('margin-left','-1%');
            $("#sideBarLeft").removeClass("col-md-2 col-sm-4 col-24").addClass("col-md-1");
            $("#bodyContent").removeClass("col-md-10 paddingLeftZero").addClass("col-md-11 paddingLeftZero");
        }
    });

    $('.toggleLeft').click(function(e) {
        if ($('.navbar-primary').hasClass('collapsed') == true) {
          $('.navbar-primary').toggleClass('collapsed');
          $('.overFlowLeft').show();
          $('#profileInfoDiv').css('margin','5% 0% 5% 0%');
          $('#logoCompany').css('margin','0px 0px 0px 0px');
          $('#bodyContent').css('margin-left','0%');
          $("#sideBarLeft").removeClass("col-md-1").addClass("col-md-2 col-sm-4 col-24");
          $("#bodyContent").removeClass("col-md-11 paddingLeftZero").addClass("col-md-10 paddingLeftZero");
        }
        else if ($('.navbar-primary').hasClass('collapsed') == false) {
            $('.navbar-primary').toggleClass('collapsed');
            $('.overFlowLeft').hide();
            $('#profileInfoDiv').css('margin','40% 0% 65% 0%');
            $('#logoCompany').css('margin','10px 0px 10px 0px');
            $('#bodyContent').css('margin-left','-1%');
            $("#sideBarLeft").removeClass("col-md-2 col-sm-4 col-24").addClass("col-md-1");
            $("#bodyContent").removeClass("col-md-10 paddingLeftZero").addClass("col-md-11 paddingLeftZero");
        }
    });

    $('.btn-expand-collapse-right').click(function(e) {
    $('.navbar-primary-right').toggleClass('collapsed-right');
    if ($('.navbar-primary-right').hasClass('collapsed-right') == true) {
      //$('#bodyContent').css('margin-right','60px');
    }
    else if ($('.navbar-primary-right').hasClass('collapsed-right') == false) {
      //$('#bodyContent').css('margin-right','200px');
    }
    });
    /* Left Sidebar Script End */
    /* Right Sidebar Script End */
    $("#sidebar").mCustomScrollbar({
        theme: "minimal"
    });

    $('#dismiss, .overlay, .dropdown-toggle').on('click', function () {
        $('#sidebar').removeClass('active');
        $('.overlay').removeClass('active');
        $('#sidebarCollapse').show();
        $('#navbarTogglerDemo02').css('margin-right','0px');
    });

    $('#sidebarCollapse').on('click', function () {
       /* if ($('#sidebar').hasClass('active')) {
            $('#sidebar').removeClass('active');
            $('.overlay').removeClass('active');
        }
        else { */
            $('#sidebarCollapse').hide();
            $('#sidebar').addClass('active');
            $('.overlay').addClass('active');
            $('.collapse.in').toggleClass('in');
            $('a[aria-expanded=true]').attr('aria-expanded', 'false');
            //$('#navbarTogglerDemo02').css('margin-right','35px');
        //}
    });

    $('#notificationIcon').on('click', function () {
        if ($('#sidebar').hasClass('active')) {
            $('#sidebar').removeClass('active');
            $('.overlay').removeClass('active');
            $('#sidebarCollapse').show();
        }
        else {
            $('#sidebarCollapse').hide();
            $('#sidebar').addClass('active');
            $('.overlay').addClass('active');
            $('.collapse.in').toggleClass('in');
            $('a[aria-expanded=true]').attr('aria-expanded', 'false');
            //$('#navbarTogglerDemo02').css('margin-right','35px');
        }
    });
    /* Right Sidebar Script End */
});