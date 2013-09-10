<h3>  <a href="/collection/{{ str(summary) }}/person/{{ name }}">{{ name }}</a> in <a href="/collection/{{ str(summary) }}">{{ str(summary) }}</a> </h3>

  {{ len(results) }} matching items <br>
  loaded from {{ c.source }}<br>
  
  <br>

  %for item in results:
  <div>
    %#{{ item.to_dict() }}
    %for tag in item.tags:
       <span class="tag">{{tag}}</span>
    %end
    <br>
    {{ item.description }}
    <br>
    <img src="file://{{ item.image }}"><br>
    %for option in item.options:
    <a href="file://{{ item.cur_path}}/{{ option }}"> {{ option }}</a><br>
    %end
  </div>
  <br>
  <br>
  %end




  <div>
  %if len(summary.available) == 1:
  [ drive available! ]
  %elif len(summary.available):
  [ {{ len(summary.available) }} drives available! ]
  %end

  </div><br>

%rebase layout title=str(summary), active="home"
