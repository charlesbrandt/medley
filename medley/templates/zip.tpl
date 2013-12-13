%for group in zips:
%for path in group:
  %if path.type() == "Image":
    <span><a href="/path/{{ str(path)[1:] }}">
    %img = path.load()
    %tiny = img.size_path("tiny")
    %small = img.size_path("small")
    <img src="/path/{{ small }}" width=147>
    %#<img src="/path/{{small.to_relative()}}" width=147>
    %#<img src="/image/{{tiny.to_relative()}}">
    %# //include image_tiny image_path = path 
    %#{{path.filename}}
    </a></span>

  %end
%end
%end

%rebase layout title="zips"
