$(document).ready(function(){
    console.log('working');

    // Keeping track of all the currently visible items.
    var currentlyShown = [];
    var index;
    var showAllButton = $('#showAll');

    // If any of the object's classes match any of the selected options, show it.
    // Using underscore.js to check for class match.
    function showRightClasses(){
        console.log('showing: ' + currentlyShown);
        if(currentlyShown.length == 0){
            showAllButton.click();
        }

        $('.hiddenpage').each(function(i){
            that = $(this);
            if( _.intersection(this.className.split(' '), currentlyShown).length > 0 ) {
                // Bring the box back and then reveal it.
                that.attr('aria-hidden','false');
                that.show();
                that.removeClass('shrunk');
            }else{
                // Shrink the box out of existence, then hide it from screen readers.
                that.addClass('shrunk');
                that.attr('aria-hidden','true');
                setTimeout(function(){
                    that.hide();
                }, 500);
            }
        });
    }

    // Desired behavior:
    // If no checkboxes are checked, check "Show All".
    // If any other checkboxes are checked, uncheck "Show All."
    // Regardless of whether someone checks or unchecks "Show All", don't change any other checkboes.

    if(showAllButton.prop('checked')){
        currentlyShown.push('hiddenpage');
        showRightClasses();
    }

    showAllButton.change(function(){
        if(!this.checked) {
            index = currentlyShown.indexOf('hiddenpage');
            if(index !== -1){ currentlyShown.splice(index, 1); }
        }else{
            currentlyShown.push('hiddenpage');
        }
        showRightClasses();
    });

    $('.pageselector').change(function(){
        subject = $(this).attr('name');
        if(!this.checked) {
            index = currentlyShown.indexOf(subject);
            if(index !== -1){ currentlyShown.splice(index, 1); }
        }else{
            currentlyShown.push(subject);
        }
        if(showAllButton.prop('checked')){
            showAllButton.click();
        }
        showRightClasses();
    });

});