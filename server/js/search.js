var Person = function(position, parent, tag, image, count, cutoffs) { 
  var self = this;
  
  self.cur_pos = ko.observable(position);
  self.parent = parent;
  self.tag = tag;
  self.image = image;
  self.count = count;
  if (cutoffs) {
    self.cutoffs = cutoffs.split(',')[0];
  }
  else {
    self.cutoffs = '';
    //console.log("Unknown cutoffs: ", cutoffs, " for ", tag); 
  }
  
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

  self.imageAuto        = ko.computed(function() {
    //show an image either way, even if we don't have one..
    //console.log("imageAuto called: " + self.tag);
    if (self.image) {
      return self.imageThumb();
    }
    else {
      return self.imageTemp();
    }
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
  
  


var SearchViewModel = function() {
  var self = this;
  
  self.cutoff = 50;
  self.names = onames;
  self.search = ko.observable('');

  self.clear_search = function() {
    self.search('');
  };

  self.number = ko.observable();
  self.results = ko.observableArray();

  self.filter = ko.computed(function() {
    //console.log("running query");
    var query = self.search().toLowerCase();
    var options = ko.utils.arrayFilter(self.names, function(name) {
      return name.toLowerCase().indexOf(query) >= 0;
    });
    self.number(options.length);
    self.results.removeAll();
    if (self.number() < self.cutoff) {
      //console.log('Pre results:');
      //console.log(self.results);
      for (var i = 0; i < self.number(); i++) {
        var cur_item = opeople[options[i]];
        //console.log(cur_item);
        var new_person = new Person(i, self, cur_item.tag, cur_item.image, cur_item.count, cur_item.cutoffs);
        //console.log(new_person);
        self.results.push(new_person);
      }
      //console.log(self.results());
    } 
  }, self);

  
};
ko.applyBindings(new SearchViewModel());


