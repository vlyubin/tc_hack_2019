function formatAnswer(rv) {
  $("#answer").text(rv[0][0]);
  $("#paragraph").text("Relevant paragraph: " + rv[0][2]);
  $("#anslink").text(rv[0][1]);
  $("#anslink").attr('href', rv[0][3]);
  $("#ansdiv").show();
}

$("#search").click(function() {
  data = {
    'query': $("#query").val()
  };
  $.ajax({
    type: "POST",
    url: '/searchwellness',
    contentType: 'application/json; charset=utf-8',
    dataType: 'json',
    data: JSON.stringify(data),
    success: function(rv) {
      console.log(rv);
      formatAnswer(rv);
    },
  });
});
