
<p>"sort" takes the specified json file, gets the latest star order from the clouds.txt file, applies that to the scenes, then groups by type.  All of this happens in application.sort_em</p>
<p>"c2" gives a way to sort the star order manually, using 10 sortable tabs</p>
<p>/compare/:collection1/:group_source1/:collection2/:group_source2</p>

<p>use:<br>
/c/other-local/browser/scripts/convert_clouds_and_jsons.py<br>
to convert current stars cloud in clouds.txt to json<br>
</p>

<p>then, move it to:<br>
/c/other/browser/collections/everything/stars.order.json<br>
</p>

<p>in browser:<br>
http://localhost:8080/compare/everything/stars.order.json/reality_kings/scenes.json.order.20120817-split<br>
</p>

<p>click to see what would happen if a group was dragged (where its items are in the other list)</p>

<p>drag the full cloud version in to new one (this will prioritize the order of the new one)<br>
lock and reload as you merge<br>
</p>

<p>remember:<br>
merged groups will get saved to a new file:<br>
merged_groups-[date].json.order<br>
update url after first save<br>
</p>

<p>can be helpful to zoom out in browser to help with drag and drop of groups</p>

%rebase layout title="HELP!", active="help"
