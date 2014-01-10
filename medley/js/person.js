//path to jquery should be defined in main page
define(['jquery', 'lodash', 'ko'], function($, _, ko) {
    /*adapted from:
      http://stackoverflow.com/questions/7218171/knockout-html5-drag-and-drop
      http://jsfiddle.net/marrok/m63aJ/
     */
var ContentModel = function() {
    var self = this;

    self.drag_start_index = ko.observable();
    self.drag_target_index = ko.observable();
    self.dragging = ko.computed(function() {
        return self.drag_start_index() >= 0;
    });
    
    //update each person in contents to have an observable position
    //then when position changes, can synchronize list with computed
    //self.people = ko.observableArray(contents);

    self.contents = ko.observableArray();
    for (var i = 0, len = contents.length; i < len; i++) {
	contents[i].cur_pos = ko.observable(i);
	//creating a writable observable for action to happen on change:
	contents[i].position = ko.computed({
	    read: function () {
		return this.cur_pos();
	    },
	    write: function (value) {
		//console.log(this);

		var cur_person = this;
		self.contents.remove(cur_person);
		self.contents.splice(value, 0, cur_person);
		self.update_pos();
		self.post();
	    },
	    //owner: this
	    owner: contents[i]
	});


	self.contents.push(contents[i]);
    }

    self.update_pos = function() {
	//finally update the position of everything
	for (var i = 0, len = self.contents().length; i < len; i++) {
	    self.contents()[i].cur_pos(i);
	};
    }

    self.change_pos = ko.computed(function() {
        return self.drag_start_index() >= 0;
    });


    self.move_to_top = function(item) {
	self.contents.remove(item);
	self.contents.splice(0, 0, item);
	self.update_pos();
	self.post();
	
    }

    self.move_to_bottom = function(item) {
	self.contents.remove(item);
	self.contents.push(item);
	self.update_pos();
	self.post();	
    }

    self.move = function(from, to) {
        if (to > self.contents().length - 1 || to < 0) return;

        var fromObj = self.contents()[from];
	self.contents.remove(fromObj);
        //var toObj = self.contents()[to];
	self.contents.splice(to, 0, fromObj);
        //self.contents()[to] = fromObj;
        //self.contents()[from] = toObj;
	self.update_pos();
        self.contents.valueHasMutated()
    }

    self.swap = function(from, to) {
        if (to > self.contents().length - 1 || to < 0) return;

        var fromObj = self.contents()[from];
        var toObj = self.contents()[to];
        self.contents()[to] = fromObj;
        self.contents()[from] = toObj;
        self.contents.valueHasMutated()
    }

    self.post = function() {
	// really only need to send the base dirs here:
	var bases = [];
	for (var i = 0, len = self.contents().length; i < len; i++) {
	    bases.push(self.contents()[i].content_base);
	}
	//console.log(self.contents());
	//console.log(bases);
	$.ajax({
	    url: 'update',
	    type: 'POST',
	    data: {
		//'people': ko.toJSON(self.contents),
		'people': JSON.stringify(bases),
	    }
	});
    };

};
ko.applyBindings(new ContentModel());
});
