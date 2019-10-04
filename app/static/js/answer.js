function formatAnswer(rv) {
  $("#answer").text(rv[0][0]);
  $("#anstitle").text("Document title: " + rv[0][1]);
  $("#paragraph").text("Relevant paragraph: " + rv[0][2]);
  $("#anslink").text(rv[0][1]);
  $("#anslink").attr('href', rv[0][3]);

  $("#l1").text(rv[1][1]);
  $("#l1").attr('href', rv[1][3]);

  $("#l2").text(rv[2][1]);
  $("#l2").attr('href', rv[2][3]);

  $("#l3").text(rv[3][1]);
  $("#l3").attr('href', rv[3][3]);

  $("#ansdiv").show();
}

$("#search").click(function() {
  data = {
    'query': $("#query").val()
  };
  $.ajax({
    type: "POST",
    url: '/search',
    contentType: 'application/json; charset=utf-8',
    dataType: 'json',
    data: JSON.stringify(data),
    success: function(rv) {
      console.log(rv);
      formatAnswer(rv);
    },
  });
});
