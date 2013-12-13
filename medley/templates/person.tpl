<h1>  <a href="/person/{{ person.tag }}">{{ person.name }}</a> </h3>

<h3 class="main_tag">{{ person.tag }}</h3>

%if person.tags:
<p>Also Known As:</p>
%include tag_block tags=person.tags
%end

<p>Similar names:</p>
    %include people_block people=related

%#<p>Content:</p>
<ul class="contents">
%for content in person.contents:
  <li class="content">
    %include content_summary content=content
  </li>
%end
</ul>

%rebase layout title=str(person.tag), active="home"
