var recommendAPI = "http://35.200.43.235:8070";
var loading = 0;

filterSelection("all") // Execute the function and show all columns
function filterSelection(c) {
    var x, i;
    x = document.getElementsByClassName("column");
    if (c == "all") c = "";
    // Add the "show" class (display:block) to the filtered elements, and remove the "show" class from the elements that are not selected
    for (i = 0; i < x.length; i++) {
        w3RemoveClass(x[i], "show");
        if (x[i].className.indexOf(c) > -1) w3AddClass(x[i], "show");
    }

    // Add active class to the current button (highlight it)
    var btns = document.getElementsByName("btn_tab");
    for (var i = 0; i < btns.length; i++) {
        btns[i].addEventListener("click", function () {
            var current = document.getElementsByClassName("active");
            current[0].className = current[0].className.replace(" active", "");
            this.className += " active";
        });
    }
}

// Show filtered elements
function w3AddClass(element, name) {
    var i, arr1, arr2;
    arr1 = element.className.split(" ");
    arr2 = name.split(" ");
    for (i = 0; i < arr2.length; i++) {
        if (arr1.indexOf(arr2[i]) == -1) {
            element.className += " " + arr2[i];
        }
    }
}

// Hide elements that are not selected
function w3RemoveClass(element, name) {
    var i, arr1, arr2;
    arr1 = element.className.split(" ");
    arr2 = name.split(" ");
    for (i = 0; i < arr2.length; i++) {
        while (arr1.indexOf(arr2[i]) > -1) {
            arr1.splice(arr1.indexOf(arr2[i]), 1);
        }
    }
    element.className = arr1.join(" ");
}

// LastFM 사용자 등록
function register() {
    (function () {
        $.getJSON(recommendAPI, {
            type: "register",
            lastfm_id: document.getElementById("lastfm_id")
        }).done(function (data) {
            var parsedJson = JSON.parse(JSON.stringify(data));
            for (var i = 1; i <= 20; i++) {
                document.getElementById("resultArea").value = document.getElementById("resultArea").value + parsedJson['recommendations'][i.toString()]['artist'] + " - " + parsedJson['recommendations'][i.toString()]['title'] + "\n";
            }

        });
    })();
}

// 추천 정보 가져오기
function getRecommendations(user) {
    (function () {
        var obj = document.getElementsByName('weather');
        var checked_weather = '';
        for (i = 0; i < obj.length; i++) {
            if (obj[i].checked) {
                checked_weather = obj[i].value;
            }
        }
        var loader = $("div.loader");
        loader.css("display", "block");
        loading = 1;
        $.getJSON(recommendAPI, {
            type: "recommend",
            user: user,
            weather: checked_weather,
            top_k: document.getElementById("top_k").value
        }).done(function (data) {
            var parsedJson = JSON.parse(JSON.stringify(data));

            if(parsedJson['result'] == "ok"){
                $('#row').empty();
                for (var i = 1; i <= parseInt(document.getElementById("top_k").value); i++) {
                    //$('#carousel:last').append('<tr><td><img src='+parsedJson['recommendations'][i.toString()]['img']+' /></td><td>' + i.toString() + '</td><td>' + parsedJson['recommendations'][i.toString()]['artist'] + '</td><td>' + parsedJson['recommendations'][i.toString()]['title'] + '</td></tr>');
                    //$('#carousel:last').append('<div class="slide"><p><a href="#"><img alt="Image Caption" width="300" height="300" src="' + parsedJson['recommendations'][i.toString()]['img'] + '"/></a><span>' + parsedJson['recommendations'][i.toString()]['artist'] + ' - ' + parsedJson['recommendations'][i.toString()]['title'] + '</span></p></div>');
                    if(parsedJson['recommendations'][i.toString()]['img'] != ''){
                        $('#row:last').append('<div class="column today"><div class="content"><img src="' + parsedJson['recommendations'][i.toString()]['img'] + '" alt="Mountains" style="width:100%"><h4>' + parsedJson['recommendations'][i.toString()]['artist'] + '</h4><p>' + parsedJson['recommendations'][i.toString()]['title'] + '</p></div></div>');
                    }else{
                        $('#row:last').append('<div class="column today"><div class="content"><img src="images/default_albumart.png" alt="Mountains" style="width:100%"><h4>' + parsedJson['recommendations'][i.toString()]['artist'] + '</h4><p>' + parsedJson['recommendations'][i.toString()]['title'] + '</p></div></div>');
                    }
                    filterSelection("all");
                    //<div class="column today"><div class="content"><img src="/w3images/mountains.jpg" alt="Mountains" style="width:100%"><h4>Mountains</h4><p>Lorem ipsum dolor..</p></div></div>
                }
            }else if(parsedJson['result'] == "nouser"){
                alert("해당 ID의 User가 존재하지 않습니다.");
            }else if(parsedJson['result'] == "nodata"){
                alert("해당 User가 이 날씨에 음악을 청취한 경험이 없습니다.");
            }
            
            var loader = $("div.loader");
            loader.css("display", "none");
            loading = 0;

            var carousel = $("#carousel").slidingCarousel();
        })
            .fail(function () {
                $('#row').empty();
                alert("통신 오류 발생");
                var loader = $("div.loader");
                loader.css("display", "none");
                loading = 0;
            });
    })();
}

$( document ).ready(function() {
    // Add active class to the current button (highlight it)
    var btns = document.getElementsByName("btn_tab");
    for (var i = 0; i < btns.length; i++) {
        btns[i].addEventListener("click", function () {
            var current = document.getElementsByClassName("active");
            current[0].className = current[0].className.replace(" active", "");
            this.className += " active";
        });
    }
});