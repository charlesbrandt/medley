<ul>
%for item in people:
  <li class="person"><a href="/person/{{ item.tag }}">{{ item.tag }}</a></li>
%end
</ul>
