//path to jquery should be defined in main page
define(['jquery', 'lodash', 'ko'], function($, _, ko) {
    /*adapted from:
      http://stackoverflow.com/questions/7218171/knockout-html5-drag-and-drop
      http://jsfiddle.net/marrok/m63aJ/
     */
var PeopleModel = function() {
    var self = this;

    self.drag_start_index = ko.observable();
    self.drag_target_index = ko.observable();
    self.dragging = ko.computed(function() {
        return self.drag_start_index() >= 0;
    });
    self.people = ko.observableArray(contents);

    self.move = function(from, to) {
        if (to > self.people().length - 1 || to < 0) return;

        var fromObj = self.people()[from];
	self.people.remove(fromObj);
        //var toObj = self.people()[to];
	self.people.splice(to, 0, fromObj);
        //self.people()[to] = fromObj;
        //self.people()[from] = toObj;
        self.people.valueHasMutated()
    }

    self.swap = function(from, to) {
        if (to > self.people().length - 1 || to < 0) return;

        var fromObj = self.people()[from];
        var toObj = self.people()[to];
        self.people()[to] = fromObj;
        self.people()[from] = toObj;
        self.people.valueHasMutated()
    }

    self.post = function() {
	// really only need to send the base dirs here:
	var bases = [];
	for (var i = 0, len = self.people().length; i < len; i++) {
	    bases.push(self.people()[i].content_base);
	}
	//console.log(self.people());
	//console.log(bases);
	$.ajax({
	    url: 'update',
	    type: 'POST',
	    data: {
		//'people': ko.toJSON(self.people),
		'people': JSON.stringify(bases),
	    }
	});
    };

};
ko.applyBindings(new PeopleModel());
});
