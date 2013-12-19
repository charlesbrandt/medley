<h1>  <a href="/person/{{ person.tag }}">{{ person.name }}</a> </h3>

<h3 class="main_tag">{{ person.tag }}</h3>

%if person.tags:
<p>Also Known As:</p>
% other_tags = person.tags[:]
% other_tags.remove(person.tag)
%include tag_block tags=other_tags
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

<script type="text/javascript">
  {{! contents }}
</script>

  <script type="text/javascript">window.JSON || document.write('<script src="js/lib/json2.js"><\/script>')</script>
    
    <script type="text/javascript" src="js/lib/require.js"></script>
    <script type="text/javascript">
      //this allows require.js to be in a different directory (lib)
      //than main custom code
      require.config({
		baseUrl: '/js',
		paths: {
			'jquery' : 'lib/jquery-2.0.3',
	                'lodash' : 'lib/lodash',
	                'ko'     : 'lib/knockout-3.0.0'
		}
      });
      require(['people'], function(people) {});
    </script>

%rebase layout title=str(person.tag), active="home"
