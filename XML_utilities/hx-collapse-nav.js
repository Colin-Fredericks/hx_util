$(document).ready(function(){
    console.log('working');

    // Keeping track of all the currently visible items.
    var currentlyShown = [];
    var index;
    var showAllButton = $('#showAll');

    // If any of the object's classes match any of the selected options, show it.
    function showRightClasses(){
        console.log('showing: ' + currentlyShown);
        if(currentlyShown.length == 0){
            showAllButton.click();
        }

        $('.hiddenpage').each(function(i){
          if( _.intersection(this.className.split(' '), currentlyShown).length > 0 ) {
              $(this).show('slow');
            }else{
              $(this).hide('slow');
            }
        });
    }

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