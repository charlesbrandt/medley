//path to jquery should be defined in main page
define(['jquery', 'lodash', 'ko', 'viewports'], function($, _, ko, vp) {

    //console.log(vp);
    //console.log("HELLLOOOOO?!?!?!");
    //http://stackoverflow.com/questions/20483627/lazyload-images-with-knockout-jquery
    ko.bindingHandlers.lazyImage = {
	update: function(element, valueAccessor, allBindingsAccessor, viewModel, bindingContext) {
            var $element     = $(element);
            // we unwrap our imageUrl to get a subscription to it,
            // so we're called when it changes.
            // Use ko.utils.unwrapObservable for older versions of Knockout
            var imageSource  = ko.unwrap(valueAccessor());
            
            $element.attr('src', imageSource);
            
	    //console.log("image source: " + imageSource);
	    
            // we don't want to remove the lazy class after the temp image
            // has loaded. Set placehold.it to something that identifies
            // your real placeholder image
            if (imageSource.indexOf('/img/blank.jpg') === -1) {
		$element.one('load', function() {
                    $(this).removeClass('lazy');
		});
            }
	}
    };
    
    var Person = function(position, parent, tag, image, count) { 
	var self = this;

	self.cur_pos = ko.observable(position);
	self.parent = parent;
	self.tag = tag;
	self.image = image;
	self.count = count;

	//creating a writable observable for action to happen on change:
	self.position = ko.computed({
	    read: function () {
		return this.cur_pos();
	    },
	    write: function (value) {
		//console.log(this);
		
		var cur_person = this;
		self.parent.items.remove(cur_person);
		self.parent.items.splice(value, 0, cur_person);
		self.parent.update_pos();
		self.parent.post();
	    },
	    //owner: this
	    owner: self
	});

	self.showPlaceholder = ko.observable(true);    
	self.imageTemp       = ko.observable('/img/blank.jpg');
	self.imageThumb      = ko.observable('/path' + self.image);
	self.imageUrl        = ko.computed(function() {
	    //console.log("imageUrl called: " + self.tag);
	    return self.showPlaceholder() ? self.imageTemp() : self.imageThumb();
	});

	self.move = function(from, to) {
            if (to > self.parent.items().length - 1 || to < 0) return;
	    
            var fromObj = self.parent.items()[from];
	    self.parent.items.remove(fromObj);
            //var toObj = self.items()[to];
	    self.parent.items.splice(to, 0, fromObj);
            //self.items()[to] = fromObj;
            //self.items()[from] = toObj;
	    self.parent.update_pos();
            self.parent.items.valueHasMutated()
	}


    };


    var Group = function(data, parent) { 
	var self = this;
	//console.log("self: " + this);

	self.parent = parent;
	
	//console.log("Adding data: " + data);
	//console.log("data length" + data.length);

	self.items = ko.observableArray();
	for (var i = 0, len = data.length; i < len; i++) {
	    var cur_item = data[i];
	    //console.log(cur_item);
	    self.items.push(new Person(i, self, cur_item.tag, cur_item.image, cur_item.count));
	    //console.log("after adding person: " + self.items().length);
	};

	//special case for empty lists:
	if (data.length === 0) {
	    console.log("No data sent, creating empty");
	    self.items.push(new Person(0, self, "empty", "no_image"));
	}

	self.update_pos = function() {
	    //finally update the position of everything
	    for (var i = 0, len = self.items().length; i < len; i++) {
		self.items()[i].cur_pos(i);
	    };
	}
	
	self.move_to_top = function(item) {
	    self.items.remove(item);
	    self.items.splice(0, 0, item);
	    self.update_pos();
	    self.post();
	}

	self.move_to_bottom = function(item) {
	    self.items.remove(item);
	    self.items.push(item);
	    self.update_pos();
	    self.post();	
	}

	self.post = function() {
	    self.parent.post();
	};

	//return self;
    };

    var Cluster = function(data) { 
	var self = this;

	self.groups = ko.observableArray();
	//console.log("groups before push: " + self.groups().length);

	for (var i = 0, len = data.length; i < len; i++) {
	    //console.log("creating group: " + data[i].length);
	    var new_group = new Group(data[i], self);
	    //console.log(new_group);
	    self.groups.push( new_group );
	};

	//console.log("groups after push: " + self.groups().length);

	self.post = function() {
	    // really only need to send the base dirs here:
	    var main = [];
	    //console.log("length: " + self.groups().length);
	    for (var i = 0; i < self.groups().length; i++) {
		//console.log("index: " + i);
		//console.log(self.groups()[i]);
		var items = self.groups()[i].items();
		var sub = [];
		for (var j = 0; j < items.length; j++) {
		    sub.push(items[j].tag);
		}
		main.push(sub);
	    }
	    //console.log(self.cluster());
	    //console.log(main);
	    $.ajax({
		url: '/people/update',
		type: 'POST',
		data: {
		    //'people': ko.toJSON(self.cluster),
		    'cluster': JSON.stringify(main),
		}
	    });
	};
	
	return self;

    };

var PeopleModel = function() {
    var self = this;

    self.drag_start_index = ko.observable();
    self.drag_target_index = ko.observable();
    self.dragging = ko.computed(function() {
        return self.drag_start_index() >= 0;
    });
    
    self.change_pos = ko.computed(function() {
        return self.drag_start_index() >= 0;
    });
	
    //update each item in contents to have an observable position
    //then when position changes, can synchronize list with computed
    //self.people = ko.observableArray(contents);

    //console.log(groups.length);
    //console.log(groups);
    self.log = function(something) {
	console.log("something: " + something);
	return something;
    }

    self.cluster = new Cluster(ogroups);
    //console.log(self.cluster.groups().length);

    self.showing = ko.observable('');
    self.show = function(what) {
	//console.log("Switching view to: " + what );
        return (function(){ self.showing(what); });
    }


};
ko.applyBindings(new PeopleModel());

var lazyInterval = setInterval(function () {
    //console.log("lazy check called");
    $('.lazy:in-viewport').each(function () {
	if (ko.dataFor(this)) {
	    //console.log(ko.dataFor(this));
            ko.dataFor(this).showPlaceholder(false);
	}
    });
}, 1000);

});
