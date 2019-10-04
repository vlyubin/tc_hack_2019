function jsUcfirst(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

function formatAnswer(rv) {
  console.log(rv);
  $("#results").append("<h2>Most likely diseases</h2><br/>");
  for (var i = 0; i < 3; i++) {
    $("#results").append("</li><h4 style='height: 56px;'>• " + jsUcfirst(rv['Disease'][i]) + " (Frequency: " + rv['Count of Disease Occurrence'][i] + ")" + "</h3></li>");
  }
}

$("#search").click(function() {
  $("#results").html("");
  symptoms = []
  Array.from($(".tag-text")).forEach(function(e) {
    symptoms.push(e.innerHTML);
  });
  data = {
    'symptoms': symptoms
  };
  $.ajax({
    type: "POST",
    url: '/symptom',
    contentType: 'application/json; charset=utf-8',
    dataType: 'json',
    data: JSON.stringify(data),
    success: function(rv) {
      console.log(rv);
      formatAnswer(rv);
    },
  });
});
