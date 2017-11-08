// We use HTML5 Web Storage to keep an out-of-date version of the grades.
// This pre-populates the skill tree. It's just a visual nicety.
function getGradesFromLocalStorage() {

	// Make sure we have local storage.
	if(typeof(Storage) !== 'undefined') {

		var assignments = [];
		var names = [];
		var scores = [];

		// Store the grade details as JSON
		if(typeof localStorage.partNames !== 'undefined'){
			assignments = JSON.parse(localStorage.hxassignments);
			names = JSON.parse(localStorage.hxnames);
			scores = JSON.parse(localStorage.hxscores);
		}

		// Log the details and call displayTree
		console.log(assignments, names, scores);
		updateOutline(assignments, names, scores);

	}else{
		console.log('No local storage');
	}

}

// If we're going to use HTML5 Web Storage, we need to store things in it.
function storeGradesToLocalStorage(assignments, names, scores){

	// Make sure we have local storage.
	if(typeof(Storage) !== "undefined") {

		// Don't bother to coerce data types.
		// Javascript will treat strings like numbers anyway with ==.
		localStorage.hxassignments = JSON.stringify(assignments);
		localStorage.hxnames = JSON.stringify(names);
		localStorage.hxscores = JSON.stringify(scores);

	}else{
		console.log('No local storage');
	}

}

function updateOutline(assignments, names, scores){
  // Add text after every line that contains assignments.
	for(i = 0; i < names.length; i++){

		currentScore = scores[i].split('%')[0];
		if(currentScore < 50){
			var imagetag = '<span class="icon fa fa-arrow-left" style="color:#cb0712" aria-hidden="true"></span>';
		}else if( currentScore < 75 ){
			var imagetag = '<span class="icon fa fa-asterisk" style="color:#ccc313" aria-hidden="true"></span>';
		}else{
			var imagetag = '<span class="icon fa fa-check" style="color:#009b00" aria-hidden="true"></span>';
		}

		gradeInfo = '<span class="gradeInfo">'
			+ ' - '
			+ assignments [i]
			+ ': '
			+ scores[i]
			+ ' '
			+ imagetag
			+ '</span>'

			var lines = $('div.nav-sub:contains('+names[i]+')')
				.filter(function(index){
					// We need not just "contains" but an exact match.
					return $(this).text().trim() === names[i];
				});
		for(j = 0; j < lines.length; j++){
			// Duplicate lines are possible. Don't append if it's already there.
			if($(lines[j]).find('.gradeInfo').length == 0){
				$(lines[j]).append(gradeInfo);
				break;
			}
		}
	}

}

// This goes through the Progress Page (loaded in the Raw HTML component), finds
// all of the grades, stores them in HTML5 local storage, and calls displayTree.
function updateScoresFromProgPage(){

	console.log('grade frame ready');
	// Turn off the loading bar.
	$('#progressbar').hide();

	var progpage = $('#yourprogress');

	// Get an array with all the text from the progress bar hovers.
	// This will need to be updated if the Progress page changes.
	var gradeText = progpage.contents().find('.xAxis span.sr').map(function() {
		return $(this).text();
  }).get();

	var assignments = [];
	var names = [];
	var scores = [];

	// This section is perhaps the most fragile. If the Progress page changes,
	// almost everything in this each() function will need to be updated.
	for(i=0; i<gradeText.length; i++){
		var bits = gradeText[i].split(' - ');
		if(bits.length == 3){
			assignments.push(bits[0]);
			names.push(bits[1]);
			scores.push(bits[2]);
		}
	}

	// Store in Web Storage and dispay on the outline.
	storeGradesToLocalStorage(assignments, names, scores);
	updateOutline(assignments, names, scores);

}

$(document).ready(function(){

	console.log('grade reader working');

	// Update from LocalStorage, if it's there.
	getGradesFromLocalStorage();

	// iFrame in the student's own progress page.
	// First, get its URL.
	var progressURL = window.url().split('/').slice(0,5).join('/') + '/progress';

	var framey = '<iframe sandbox="allow-same-origin allow-scripts allow-popups allow-forms" aria-hidden="true" id="yourprogress" title="Your Progress Page" src="' + progressURL + '" style="height: 0px; border: none; margin-left: 40000px;" scrolling="no">Your browser does not support IFrames.</iframe>';
	$($('.xblock')[0]).append($(framey));

	var cannotLoad = setTimeout(function(){
		$('#progressbar').text('Unable to load your scores.');
	}, 10000);

    // Once the progress page loads, update the outline with grades.
	$('iframe#yourprogress').load(function() {
		clearTimeout(cannotLoad);
		updateScoresFromProgPage();
	});


});
