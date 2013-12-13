<link href="/css/video-js.css" rel="stylesheet">
<script src="/js/libs/video.js"></script>
<script>
  videojs.options.flash.swf = "/js/libs/video-js.swf"
</script>

<div class="content">
%if content.image:
<div><img src="/path/{{content.image}}"></div>
%end
<b>{{ content.title }}</b>

<ul>
%for tag in content.people:
  <li class="person"><a href="/person/{{ tag }}">{{ tag }}</a></li>
%end
</ul>

%#<p>Tags:</p>
%include tag_block tags=content.tags


<p>{{ content.description }}</p>

%#<p>Via: <a href="/collection/{{ content.remainder['collection'] }}">{{ content.remainder['collection'] }}</a></p>
%#<p>available? {{ content.available }}</p>

%#<p>{{ content.remainder }}</p>
%#<p>{{ content.debug() }}</p>

%for movie in content.movies:
  <li class="movie">
    {{movie}}
  </li>
%end

%for zip in content.zips:
  <li class="zip">
    <a href="/collection/{{ collection }}/zip/{{ content.base_dir }}">    {{zip}}
  </li>
%end


</div>
%rebase layout title=str(content.title)
