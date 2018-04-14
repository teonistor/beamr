(function() {
  var img = $('img').filter(function(){return $(this).attr('src').indexOf('snapshot')>-1});
  var par = img.parent().prev();

  par.addClass('row')
  par.children().addClass('col-sm-7')
  img.addClass('col-sm-5')

  $.each(img, function(i, x){
    par.get(i).append(x)
  });
})();
