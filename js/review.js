// submit merge
var token;
get_user_token = function() {
    return $.ajax({
        url: constant.HOST_IP + "/login/get_user_info",
        dataType: "json",
        success: function(data) {
            var ref;
            if (data.failed) {
                return console.err(data.result);
            } else if (data != null ? (ref = data.result) != null ? ref.token : void 0 : void 0) {
                console.log("hello: " + data.result.username);
                token = data.result.token;
                get_review_details();
            } else {
                return console.log("failed to get user token");
            }
        }
    });
};

$(document).ready(function() {
    $("#button").click(function() {
        var review_id = $.parseParams(location.search.substr(1))['id'];
        var operator = document.getElementById("operator").value;
        var post_data = {
            "operator": operator
        };
        $.ajax({
            cache: false,
            type: "POST",
            url: constant.HOST_IP + constant.API_VERSION + '/merge/' + review_id,
            //提交的URL
            data: post_data,
            async: false,
            headers: {
                "Access-Token": token
            },
            dataType: "json",
            success: function(data) {
                if (data.failed == true) {
                    alert(data.result);
                } else {
                    alert("Successfully");
                    window.location.replace("review.html?id=" + review_id);
                }
            },
            error: function(request) {
                alert("Connection error.");
            }
        });
    });
});

// abandon review
$(document).ready(function() {
    $("#abandon").click(function() {
        var review_id = $.parseParams(location.search.substr(1))['id'];
        var operator = document.getElementById("operator").value;
        var post_data = {
            "operator": operator
        };
        $.ajax({
            cache: false,
            type: "POST",
            url: constant.HOST_IP + constant.API_VERSION + '/abandon/' + review_id,
            //提交的URL
            data: post_data,
            async: false,
            headers: {
                "Access-Token": token
            },
            dataType: "json",
            success: function(data) {
                if (data.failed == true) {
                    alert(data.result);
                } else {
                    alert("Successfully");
                    window.location.replace("review.html?id=" + review_id);
                }
            },
            error: function(request) {
                alert("Connection error.");
            }
        });
    });
});

// retrigger review
$(document).ready(function() {
    $("#retrigger").click(function() {
        var review_id = $.parseParams(location.search.substr(1))['id'];
        var operator = document.getElementById("operator").value;
        var post_data = {
            "operator": operator
        };
        $.ajax({
            cache: false,
            type: "POST",
            url: constant.HOST_IP + constant.API_VERSION + '/retrigger_review/' + review_id,
            //提交的URL
            data: post_data,
            async: false,
            headers: {
                "Access-Token": token
            },
            dataType: "json",
            success: function(data) {
                if (data.failed == true) {
                    alert(data.result);
                } else {
                    alert("Successfully");
                    window.location.replace("review.html?id=" + review_id);
                }
            },
            error: function(request) {
                alert("Connection error.");
            }
        });
    });
});

// submit comment
$(document).ready(function() {
    $("#submit").click(function() {
        var review_id = $.parseParams(location.search.substr(1))['id'];
        var submitter = document.getElementById("comment_submitter").value;
        var content = document.getElementById("user_comment").value;
        var score = document.getElementById("comment_score").value;
        var verified = document.getElementById("comment_verified").value;
        var post_data = {
            "submitter": submitter,
            "content": content,
            "score": score,
            "verified": verified
        };
        $.ajax({
            cache: false,
            type: "POST",
            url: constant.HOST_IP + constant.API_VERSION + '/comment/' + review_id,
            //提交的URL
            data: post_data,
            async: false,
            headers: {
                "Access-Token": token
            },
            dataType: "json",
            success: function(data) {
                if (data.failed == true) {
                    alert(data.result);
                } else {
                    alert("Successfully");
                    window.location.replace("review.html?id=" + review_id);
                }
            },
            error: function(request) {
                alert("Connection error.");
            }
        });
    });
});

// show review details
get_review_details = function() {
    var HOST;
    var review_id = $.parseParams(location.search.substr(1))['id'];

    HOST = constant.HOST_IP + constant.API_VERSION;

    $.ajax({
        url: HOST + "/review/" + review_id,
        //提交的URL
        headers: {
            "Access-Token": token
        },
        dataType: "json",
        success: function(data) {
            if (data.failed) {
                alert(data.result);
            }
            review = data.result;
            console.log(review);

            document.getElementById("topic").innerHTML = review.topic;
            // TODO: Different colors for different status
            if (review.status == "open") {
                $('#status').addClass("success");
            } else {
                if (review.status == "closed") {
                    $('#status').addClass("info");
                } else if (review.status == "abandon") {
                    $('#status').addClass("danger");
                }

                // Disable merge and anandon 
                document.getElementById("submit_div").style.display = "none";
                document.getElementById("abandon").style.display = "none";
            }
            document.getElementById("status").innerHTML = review.status;
            document.getElementById("submit_user").innerHTML = review.submitter;
            document.getElementById("submit_date").innerHTML = getLocalTime(review.submit_timestamp);
            document.getElementById("base").innerHTML = "<a href='" + review.base + "' target='_blank'> " + review.base + " " + review.base_codename + "</a>";
            document.getElementById("rpa").innerHTML = "<a href='" + review.rpa + "' target='_blank'> " + review.rpa + " " + review.rpa_codename + "</a>";
            document.getElementById("description").innerHTML = line2br(review.comment);

            var cm_content = "";
            var check_result = "";
            if (review.comments == undefined) {
                return;
            }
            $.each(review.comments,
                function(i, comment_item) {
                    if (comment_item.submitter == 'checkupdate' && comment_item.verified == 1) {
                        check_result = comment_item.content;
                    }
                    console.log(check_result);
                    cm_content = cm_content + "<div class='panel panel-default' style='border: none;'>";
                    cm_content = cm_content + "<div class='panel-heading' role='tab' id='heading" + i + "'>";
                    cm_content = cm_content + "<h4 class='panel-title'>";
                    cm_content = cm_content + "<div style='text-decoration: none; display:block;";
                    // colors of link
                    if (comment_item.verified == 1) {
                        cm_content = cm_content + "color: green"
                    } else if (comment_item.verified == -1) {
                        cm_content = cm_content + "color: red"
                    } else if (comment_item.score == 1) {
                        cm_content = cm_content + "color: #2e64fe"
                    } else if (comment_item.score == -1) {
                        cm_content = cm_content + "color: #ff5858"
                    }
                    cm_content = cm_content + ";'"

                    cm_content = cm_content + " role='button' data-toggle='collapse' data-parent='#accordion' href='#collapse" + i + "' aria-expanded='false' aria-controls='collapse" + i + "'>";
                    cm_content = cm_content + "<div class='col-xs-3'>" + comment_item.submitter + "</div>";

                    if (comment_item.content.length > 50) {
                        cm_content = cm_content + "<div class='center' style='display:inline;'>" + removeHTMLtag(comment_item.content).substring(0, 50) + "...";
                    } else {
                        cm_content = cm_content + "<div class='center' style='display:inline;'>" + removeHTMLtag(comment_item.content);
                    }

                    cm_content = cm_content + "<div style='display:inline;float:right;'>" + getLocalTime(comment_item.create_timestamp) + "</div></div>";
                    cm_content = cm_content + "</div></h4></div>";
                    cm_content = cm_content + "<div id='collapse" + i + "' class='panel-collapse collapse' role='tabpanel' aria-labelledby='heading" + i + "'>";
                    cm_content = cm_content + "<div class='panel-body'>";

                    if (comment_item.score != 0) {
                        m_content = cm_content + " Score: " + comment_item.score + "<br>";
                    }
                    if (comment_item.verified != 0) {
                        cm_content = cm_content + "Verified: " + toboolean(comment_item.verified) + "<br>";
                    }

                    cm_content = cm_content + line2br(comment_item.content);
                    cm_content = cm_content + "</div></div></div>"

                });
            document.getElementById("accordion").innerHTML = cm_content;
            // parse checkupdate result
            parseCheckresult(check_result);
        }
    });
};

function parseCheckresult(check_result) {
    var pack_list = ""
    var pack_add = []
    var pack_update = []

    var regExp = /href="(.*?)"/g;
    var arr = check_result.match(regExp);
    console.log(arr);
    json_url = arr[0].replace('href="', '').replace('"', '');

    // $.getJSON(json_url + "/result.json", function (data) {
    //     console.log(data)
    //     $.each(data.details, function (i, pack_item) {
    //         if (pack_item.type == 'add') {
    //             // TODO: one package in amd64 and i386, should be done in result.json, not in js
    //             if ( notContain(pack_item.name, pack_add) ) {
    //                 pack_add.push(pack_item)
    //             }        
    //         }
    //         else if (pack_item.type == 'update') {
    //             if ( notContain(pack_item.name, pack_update) ) {
    //                 pack_update.push(pack_item)
    //             }
    //         }
    //     });
    //     // check update result
    //     if (pack_add.length + pack_update.length > 0) {
    //         pack_list = "<div>This review adds <b>" + pack_add.length + "</b> package(s) and updates <b>" + pack_update.length +"</b> package(s).</div>";
    //         // packages add
    //         if (pack_add.length > 0) {
    //             pack_list = pack_list + "<div><h4>Add package(s):</h4></div>"
    //             for (var i=0;i< pack_add.length;i++)
    //             {
    //                 pack_list = pack_list + "<div style='clear:both;' class='col-xs-3'><b>" + pack_add[i].name + "</b></div>";
    //                 pack_list = pack_list + "<div class='col-xs-2'>New version: </div><div class='col-xs-2'><b>" + pack_add[i].newversion + "</b></div>";
    //             }
    //         }
    //         // packages update
    //         if (pack_update.length > 0) {
    //             pack_list = pack_list + "<div style='clear:both;'><h4>Update package(s):</h4></div>"
    //             for (var i=0;i< pack_update.length;i++)
    //             {
    //                 pack_list = pack_list + "<div style='clear:both;' class='col-xs-3'><b>" + pack_update[i].name + "</b></div>";
    //                 pack_list = pack_list + "<div class='col-xs-2'>New version: </div><div class='col-xs-2'><b>" + pack_update[i].newversion + "</b></div><div class='col-xs-2'>Old version:</div><div class='col-xs-2'>  " + pack_update[i]. oldversion+ "</div>";
    //             }
    //         }
    //     }
    //     else {
    //         pack_list = "<div>This review adds <b>" + pack_add.length + "</b> package(s) and updates <b>" + pack_update.length +"</b> package(s).</div>";
    //         if (pack_add.length > 0) {
    //             pack_list = pack_list + "<div><h4>Add package(s):</h4></div>"
    //         }
    //         if (pack_update.length > 0) {
    //             pack_list = pack_list + "<div style='clear:both;'><h4>Update package(s):</h4></div>"
    //         }
    //     }
    //     document.getElementById("checkresult").innerHTML = line2br(pack_list);
    // });
    document.getElementById("checkresult").innerHTML = "<a target='_blank' href=" + json_url + ">" + json_url + "</a>";
}

init_all = function() {
    get_user_token();
};

init_all();