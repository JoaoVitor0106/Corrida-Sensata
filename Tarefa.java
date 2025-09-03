package ucb.aplicativo.model;
import java.time.LocalDateTime;

public class Tarefa {
    private Long id;
    private String titulo;
    private String descricao;
    private LocalDateTime datahora;
    private boolean completa;
    
    // Construtor padrão
    public Tarefa() {
        this.datahora = LocalDateTime.now();
        this.completa = false;
    }
    
    // Construtor para nova tarefa
    public Tarefa(String titulo, String descricao) {
        this(); 
        this.titulo = titulo;
        this.descricao = descricao;
    }

    // Construtor completo
    public Tarefa(Long p_id, String p_titulo, String p_descricao, LocalDateTime p_datahora, boolean p_completa) {
        this.id = p_id; 
        this.titulo = p_titulo;
        this.descricao = p_descricao;
        this.datahora = p_datahora;
        this.completa = p_completa;
    }
}