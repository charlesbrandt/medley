//path to jquery should be defined in main page
//define(['jquery', 'lodash', 'ko'], function($, _, ko) {
/*adapted from:
    http://stackoverflow.com/questions/7218171/knockout-html5-drag-and-drop
    http://jsfiddle.net/marrok/m63aJ/
  */
$('.expand-one').click(function() {
  $('.content-one').slideToggle('slow');
});

$('#show-photos').click(function() {
  $('#photos').slideToggle('slow');
});

$('#show-media').click(function() {
  $('#content').slideToggle('slow');
});

$('#toggle-layout').click(function() {
  $('#content').toggleClass('top-bottom-columns');
});

function toDraggables(values) {
  return ko.utils.arrayMap(values, function (value) {
    return {
      value: value,
      dragging: ko.observable(false),
      isSelected: ko.observable(false)
    };
  });
}

function SortableView(items) {
  items = items || [];
  this.items = ko.observableArray([].concat(items));
}
  
SortableView.prototype.dragStart = function (item) {
  item.dragging(true);
};

SortableView.prototype.dragEnd = function (item) {
  item.dragging(false);
};
  
SortableView.prototype.reorder = function (event, dragData, zoneData) {
  if (dragData !== zoneData.item) {
    //console.log(zoneData);
    var zoneDataIndex = zoneData.items.indexOf(zoneData.item);
    zoneData.items.remove(dragData);
    zoneData.items.splice(zoneDataIndex, 0, dragData);
  }
};


var ContentModel = function() {
  var self = this;

  self.photo_bases = [];

  self.scrollWhileDragging = new SortableView(toDraggables(photos));
  self.scrollWhileDragging.dragEnd = function (item) {
    item.dragging(false);
    self.update_photos();
    self.post();
  };

  self.update_photos = function() {
    self.photo_bases = [];
    var cur_photos = self.scrollWhileDragging.items;
    for (i = 0, len = cur_photos().length; i < len; i++) {
      self.photo_bases.push(cur_photos()[i].value.base_dir + '/' + cur_photos()[i].value.filename);
    }
  };
  self.update_photos();

  //list of positions that mark different cut off points
  //self._cutoffs = cur_person.cutoffs;
  //self._cutoffs = "test";

  self._cutoffs = ko.observable(cur_person.cutoffs);

  self.editing_cutoffs = ko.observable(false);
  self.edit_cutoffs = function() {
    //console.log("Changing editing_cutoffs");
    self.editing_cutoffs(true);

    /*
      if (self.editing_cutoffs()) {
      self.editing_cutoffs(false);
      }
      else {
      self.editing_cutoffs(true);
      }
    */
  };
  self.cutoffs = ko.computed({
    read: function() {
      return self._cutoffs();
    },
    write: function(value) {
      //console.log(this);
      //console.log("changing cutoffs value: ", value);
      //self._cutoffs = value;
      self._cutoffs(value);
      self.post();
      //console.log(self._cutoffs());
    },
    owner: self
  });


  self._cutoff_tags = ko.observable(cur_person.cutoff_tags);
  self.editing_cutoff_tags = ko.observable(false);
  self.edit_cutoff_tags = function() {
    self.editing_cutoff_tags(true);
  };
  self.cutoff_tags = ko.computed({
    read: function() {
      return self._cutoff_tags();
    },
    write: function(value) {
      self._cutoff_tags(value);
      self.post();
    },
    owner: self
  });


  self.merged_cutoffs = ko.computed(function() {
    //combine cutoffs with associated tag for better readability
    var cots = self.cutoff_tags().split(',');
    var cos = self.cutoffs().split(',');
    var combined = '';
    for (var i = 0; i < cos.length; i++) {
      combined += cots[i] + ':' + cos[i] + ', ';
    }
    return combined;
  });



  self._default_cutoff = ko.observable(cur_person.default_cutoff);
  self.editing_default_cutoff = ko.observable(false);
  self.edit_default_cutoff = function() {
    self.editing_default_cutoff(true);
  };
  self.default_cutoff = ko.computed({
    read: function() {
      return self._default_cutoff();
    },
    write: function(value) {
      self._default_cutoff(value);
      self.post();
    },
    owner: self
  });

  self._default_cutoff_tag = ko.observable(cur_person.default_cutoff_tag);
  self.editing_default_cutoff_tag = ko.observable(false);
  self.edit_default_cutoff_tag = function() {
    self.editing_default_cutoff_tag(true);
  };
  self.default_cutoff_tag = ko.computed({
    read: function() {
      return self._default_cutoff_tag();
    },
    write: function(value) {
      self._default_cutoff_tag(value);
      self.post();
    },
    owner: self
  });


  self._links = ko.observable(cur_person.links);
  self.editing_links = ko.observable(false);
  self.edit_links = function() {
    self.editing_links(true);
  };
  self.link_lines = ko.computed(function() {
    //var result = '';
    var generated = [];
    var lines = self._links().match(/[^\r\n]+/g);
    if (lines) {
      var cur_line;
      for (var i = 0; i < lines.length; i++) {
        cur_line = lines[i];
        //http://stackoverflow.com/questions/8498592/extract-root-domain-name-from-string
        var matches = cur_line.match(/^https?\:\/\/([^\/?#]+)(?:[\/?#]|$)/i);
        var domain = matches && matches[1]; // domain will be null if no match is found
        generated.push('<a href="' + cur_line + '">' + domain + '</a>');
      }
    }

    return generated;

  });
  self.links = ko.computed({
    read: function() {
      return self._links();
    },
    write: function(value) {
      self._links(value);
      console.log('calling post()');
      self.post();
    },
    owner: self
  });

  self._notes = ko.observable(cur_person.notes);
  self.editing_notes = ko.observable(false);
  self.edit_notes = function() {
    self.editing_notes(true);
  };
  self.notes = ko.computed({
    read: function() {
      return self._notes();
    },
    write: function(value) {
      self._notes(value);
      self.post();
    },
    owner: self
  });

  self.photo_tags = ko.observable();
  self.photo_urls = ko.observable();
  self.editing_downloads = ko.observable(false);
  self.toggle_downloads = function() {
    //console.log("toggling downloads");
    //console.log(self.editing_downloads());
    if (self.editing_downloads()) {
      self.editing_downloads(false);
    }
    else { 
      self.editing_downloads(true);
    }
    //console.log(self.editing_downloads());
  };

  self.do_download = function() {
    console.log(self.photo_urls());
    console.log(self.photo_tags());
    $.ajax({
      url: 'download_images',
      type: 'POST',
      data: {
        'urls': self.photo_urls(),
        'tags': JSON.stringify(self.photo_tags())
      }
    });
  };

  self._similar = ko.observable(cur_person.similar_to);
  self.editing_similar = ko.observable(false);
  self.edit_similar = function() {
    self.editing_similar(true);
  };
  self.similar = ko.computed({
    read: function() {
      return self._similar();
    },
    write: function(value) {
      self._similar(value);
      //self.make_similar_links();
      self.post();
    },
    owner: self
  });


  self.similar_links = ko.observable();

  self.make_similar_links = ko.computed(function() {
    console.log(self.similar());
    if (self.similar()) {
      var items = self.similar().split(',');
      //items.pop();
      console.log(items);

      var result = '';
      for (var i = 0; i < items.length; i++) {
        result += '<a href="/person/' + items[i] + '/">' + items[i] + '</a>,';
      }
      console.log(result);
      self.similar_links(result);
    };
  });

  //console.log(self.similar_links());

  //console.log(self.editing_cutoffs());
  //console.log(!self.editing_cutoffs());


  self.drag_start_index = ko.observable();
  self.drag_target_index = ko.observable();
  self.dragging = ko.computed(function() {
    return self.drag_start_index() >= 0;
  });

  /*
  //modeling after contents array
  console.log(photos);
  self.photos = ko.observableArray();
  for (var i = 0, len = photos.length; i < len; i++) {
    photos[i].cur_pos = ko.observable(i);
    //creating a writable observable for action to happen on change:
    photos[i].position = ko.computed({
      read: function() {
        return this.cur_pos();
      },
      write: function(value) {
        //console.log(this);

        var cur_photo = this;
        self.photos.remove(cur_photo);
        self.photos.splice(value, 0, cur_photo);
        self.update_pos();
        self.post();
      },
      //owner: this
      owner: photos[i]
    });

    self.photos.push(photos[i]);
  }
  */


  //console.log(contents);

  //update each person in contents to have an observable position
  //then when position changes, can synchronize list with computed
  //self.people = ko.observableArray(contents);

  self.contents = ko.observableArray();
  for (var i = 0, len = contents.length; i < len; i++) {
    contents[i].cur_pos = ko.observable(i);
    //creating a writable observable for action to happen on change:
    contents[i].position = ko.computed({
      read: function() {
        return this.cur_pos();
      },
      write: function(value) {
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


  self.post = function() {
    // really only need to send the base dirs here:
    var content_bases = [];
    for (var i = 0, len = self.contents().length; i < len; i++) {
      content_bases.push(self.contents()[i].base_dir);
    }

    //console.log(self.contents());
    //console.log(content_bases);

    //console.log(self.photo_bases);

    $.ajax({
      url: 'update',
      type: 'POST',
      data: {
        //'people': ko.toJSON(self.contents),
        'contents': JSON.stringify(content_bases),
        'cutoffs': JSON.stringify(self.cutoffs()),
        'cutoff_tags': JSON.stringify(self.cutoff_tags()),
        'default_cutoff_tag': JSON.stringify(self.default_cutoff_tag()),
        'default_cutoff': JSON.stringify(self.default_cutoff()),
        'links': JSON.stringify(self.links()),
        'notes': JSON.stringify(self.notes()),
        'similar': JSON.stringify(self.similar()),
        'photos': JSON.stringify(self.photo_bases)
      }
    });
    //console.log('Post Called');
  };

  self.update_pos = function() {
    //finally update the position of everything
    for (var i = 0, len = self.contents().length; i < len; i++) {
      self.contents()[i].cur_pos(i);
    };
  };

  self.change_pos = ko.computed(function() {
    return self.drag_start_index() >= 0;
  });


  self.move_to_top = function(item) {
    self.contents.remove(item);
    self.contents.splice(0, 0, item);
    self.update_pos();
    self.post();

  };

  self.move_to_bottom = function(item) {
    self.contents.remove(item);
    self.contents.push(item);
    self.update_pos();
    self.post();
  };

  self.move = function(from, to) {
    if (to > self.contents().length - 1 || to < 0) return;

    var fromObj = self.contents()[from];
    self.contents.remove(fromObj);
    //var toObj = self.contents()[to];
    self.contents.splice(to, 0, fromObj);
    //self.contents()[to] = fromObj;
    //self.contents()[from] = toObj;
    self.update_pos();
    self.contents.valueHasMutated();
  };

  self.swap = function(from, to) {
    if (to > self.contents().length - 1 || to < 0) return;

    var fromObj = self.contents()[from];
    var toObj = self.contents()[to];
    self.contents()[to] = fromObj;
    self.contents()[from] = toObj;
    self.contents.valueHasMutated();
  };

};
ko.applyBindings(new ContentModel());

//console.log("made it here");
//});
