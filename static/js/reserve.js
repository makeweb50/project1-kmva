$(document).ready(function() {
 
    $('#login').click( function(event){
        event.preventDefault();
        $('#overlay').fadeIn(400, // анимируем показ обложки
            function(){ // далее показываем мод. окно
                $('#login_modal') 
                    .css('display', 'block')
                    .animate({opacity: 1, top: '50%'}, 200);
        });
    });
  
   $('#signup').click( function(event){
        event.preventDefault();
        $('#overlay').fadeIn(400, // анимируем показ обложки
            function(){ // далее показываем мод. окно
                $('#signup_modal') 
                    .css('display', 'block')
                    .animate({opacity: 1, top: '50%'}, 200);
        });
    });
 
    // закрытие модального окна
  
    var closeModal =  function(){
        $('#login_modal, #signup_modal')
            .animate({opacity: 0, top: '45%'}, 200,  // уменьшаем прозрачность
                function(){ // пoсле aнимaции
                    $(this).css('display', 'none'); // скрываем окно
                    $('#overlay').fadeOut(400); // скрывaем пoдлoжку
                }
            );
    };
    // при нажатии на кнопку закрытия или на подложку 
    $('.modal_close, #overlay').on('click', closeModal);
  
    // при нажатии на кнопку Esc
    $(document).keyup(function(evt) {
      if (evt.keyCode == 27) {
         closeModal();
      }
    });
 
  
    /***$('#search').on('keyup', function(){
      
      let value = $("#search").val();
      
      console.log(value);
      $.getJSON("/search", {
        value:value
      })
      .done(function(data, textStatus, jqXHR){
        let content = "<ul>";
        for(let i=0; i<data.length; i++) {
          content += "<li>"+data[0][i]+"</li>";
        }
        
        content += "</ul>"
        $('#result').html(content);
      })
      .fail(function(jqXHR, textStatus, errorThrown) {
        console.log(errorThrown.toString());
      });
    })*///
    
});