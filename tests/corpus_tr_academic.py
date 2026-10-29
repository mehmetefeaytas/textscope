"""A deterministic Turkish academic-prose corpus for rule-table scanning.

The corpus is built from sentence templates, not typed by hand 250 times. Every
template is a complete grammatical frame; the slots are domain-specific noun
phrases that already carry the case suffix the frame needs. That keeps the
generated paragraphs well formed while still covering ten domains, twelve
registers and three prose styles.

Nothing here is random: ``SAMPLES`` is byte-identical on every import and on
every Python version, so scan counts are reproducible.
"""

from __future__ import annotations

REGISTERS: list[str] = [
    "thesis_intro",
    "literature_review",
    "methodology",
    "findings",
    "discussion",
    "conclusion",
    "limitations",
    "abstract",
    "ethics_statement",
    "grant_proposal",
    "conference_abstract",
    "peer_review",
]

DOMAINS: list[dict[str, str]] = [
    {
        "domain": "education",
        "topic": "uzaktan eğitim uygulamaları",
        "tgen": "uzaktan eğitim uygulamalarının",
        "tloc": "uzaktan eğitim uygulamalarında",
        "tdat": "uzaktan eğitim uygulamalarına",
        "field": "eğitim bilimleri",
        "pop": "öğretmenler",
        "pgen": "öğretmenlerin",
        "method": "karma yöntem",
        "mgen": "karma yöntemin",
        "sloc": "devlet okullarında",
        "sdat": "devlet okullarına",
        "unit": "okul",
        "unit_pl": "okullar",
    },
    {
        "domain": "health_sciences",
        "topic": "hasta bakım süreçleri",
        "tgen": "hasta bakım süreçlerinin",
        "tloc": "hasta bakım süreçlerinde",
        "tdat": "hasta bakım süreçlerine",
        "field": "sağlık bilimleri",
        "pop": "hemşireler",
        "pgen": "hemşirelerin",
        "method": "tanımlayıcı araştırma",
        "mgen": "tanımlayıcı araştırmanın",
        "sloc": "eğitim ve araştırma hastanelerinde",
        "sdat": "eğitim ve araştırma hastanelerine",
        "unit": "klinik",
        "unit_pl": "klinikler",
    },
    {
        "domain": "engineering",
        "topic": "betonarme yapılar",
        "tgen": "betonarme yapıların",
        "tloc": "betonarme yapılarda",
        "tdat": "betonarme yapılara",
        "field": "inşaat mühendisliği",
        "pop": "saha mühendisleri",
        "pgen": "saha mühendislerinin",
        "method": "sonlu elemanlar yöntemi",
        "mgen": "sonlu elemanlar yönteminin",
        "sloc": "pilot bölgelerde",
        "sdat": "pilot bölgelere",
        "unit": "yapı",
        "unit_pl": "yapılar",
    },
    {
        "domain": "economics",
        "topic": "küçük ve orta ölçekli işletmeler",
        "tgen": "küçük ve orta ölçekli işletmelerin",
        "tloc": "küçük ve orta ölçekli işletmelerde",
        "tdat": "küçük ve orta ölçekli işletmelere",
        "field": "iktisat",
        "pop": "işletme yöneticileri",
        "pgen": "işletme yöneticilerinin",
        "method": "panel veri analizi",
        "mgen": "panel veri analizinin",
        "sloc": "imalat sanayinde",
        "sdat": "imalat sanayine",
        "unit": "firma",
        "unit_pl": "firmalar",
    },
    {
        "domain": "sociology",
        "topic": "kent yoksulluğu",
        "tgen": "kent yoksulluğunun",
        "tloc": "kent yoksulluğunda",
        "tdat": "kent yoksulluğuna",
        "field": "sosyoloji",
        "pop": "mahalle sakinleri",
        "pgen": "mahalle sakinlerinin",
        "method": "derinlemesine görüşme",
        "mgen": "derinlemesine görüşmenin",
        "sloc": "göç alan mahallelerde",
        "sdat": "göç alan mahallelere",
        "unit": "hane",
        "unit_pl": "haneler",
    },
    {
        "domain": "psychology",
        "topic": "sosyal kaygı",
        "tgen": "sosyal kaygının",
        "tloc": "sosyal kaygıda",
        "tdat": "sosyal kaygıya",
        "field": "psikoloji",
        "pop": "ergenler",
        "pgen": "ergenlerin",
        "method": "boylamsal tarama",
        "mgen": "boylamsal taramanın",
        "sloc": "ortaöğretim kurumlarında",
        "sdat": "ortaöğretim kurumlarına",
        "unit": "katılımcı",
        "unit_pl": "katılımcılar",
    },
    {
        "domain": "computer_science",
        "topic": "makine öğrenmesi modelleri",
        "tgen": "makine öğrenmesi modellerinin",
        "tloc": "makine öğrenmesi modellerinde",
        "tdat": "makine öğrenmesi modellerine",
        "field": "bilgisayar mühendisliği",
        "pop": "yazılım geliştiricileri",
        "pgen": "yazılım geliştiricilerinin",
        "method": "deneysel değerlendirme",
        "mgen": "deneysel değerlendirmenin",
        "sloc": "açık kaynak projelerde",
        "sdat": "açık kaynak projelere",
        "unit": "model",
        "unit_pl": "modeller",
    },
    {
        "domain": "environmental_science",
        "topic": "kentsel su yönetimi",
        "tgen": "kentsel su yönetiminin",
        "tloc": "kentsel su yönetiminde",
        "tdat": "kentsel su yönetimine",
        "field": "çevre bilimleri",
        "pop": "yerel yöneticiler",
        "pgen": "yerel yöneticilerin",
        "method": "yaşam döngüsü değerlendirmesi",
        "mgen": "yaşam döngüsü değerlendirmesinin",
        "sloc": "havza alanlarında",
        "sdat": "havza alanlarına",
        "unit": "havza",
        "unit_pl": "havzalar",
    },
    {
        "domain": "law",
        "topic": "kişisel verilerin korunması",
        "tgen": "kişisel verilerin korunmasının",
        "tloc": "kişisel verilerin korunmasında",
        "tdat": "kişisel verilerin korunmasına",
        "field": "hukuk",
        "pop": "hukuk uzmanları",
        "pgen": "hukuk uzmanlarının",
        "method": "doktrinel inceleme",
        "mgen": "doktrinel incelemenin",
        "sloc": "ulusal yargı kararlarında",
        "sdat": "ulusal yargı kararlarına",
        "unit": "karar",
        "unit_pl": "kararlar",
    },
    {
        "domain": "business",
        "topic": "dijital dönüşüm stratejileri",
        "tgen": "dijital dönüşüm stratejilerinin",
        "tloc": "dijital dönüşüm stratejilerinde",
        "tdat": "dijital dönüşüm stratejilerine",
        "field": "işletme",
        "pop": "orta kademe yöneticiler",
        "pgen": "orta kademe yöneticilerin",
        "method": "örnek olay incelemesi",
        "mgen": "örnek olay incelemesinin",
        "sloc": "holding şirketlerinde",
        "sdat": "holding şirketlerine",
        "unit": "birim",
        "unit_pl": "birimler",
    },
]

# role -> (nominalised style, plain style)
_SENTENCES: dict[str, dict[str, tuple[str, str]]] = {
    "thesis_intro": {
        "intro": (
            "Son yıllarda {topic}, {field} alanında giderek daha fazla tartışılan bir konu hâline gelmiştir.",
            "Son yıllarda {topic} hem uygulamada hem de {field} alanında daha sık tartışılıyor.",
        ),
        "gap": (
            "Var olan çalışmaların büyük bölümü {tloc} kısa vadeli etkileri ele almakta, uzun vadeli sonuçları ise yeterince incelememektedir.",
            "Var olan çalışmaların çoğu {tloc} yalnızca kısa vadeli etkileri ele alıyor, uzun vadeli sonuçları ise yeterince incelemiyor.",
        ),
        "aim": (
            "Bu çalışmanın amacı, {tgen} {sloc} nasıl işlediğini {method} aracılığıyla ortaya koymaktır.",
            "Bu çalışmada {tgen} {sloc} nasıl işlediğini {method} ile ortaya koymayı amaçladık.",
        ),
        "method": (
            "Araştırma kapsamında {sloc} yer alan {pop} ile {method} kullanılarak veri toplanmıştır.",
            "Araştırma kapsamında {sloc} yer alan {pop} ile {method} kullanarak veri topladık.",
        ),
        "finding": (
            "Bulgular, {tloc} birbirinden farklı üç eğilimin öne çıktığını göstermektedir.",
            "Bulgular {tloc} birbirinden farklı üç eğilimin öne çıktığını gösteriyor.",
        ),
        "discussion": (
            "Elde edilen sonuçlar, {field} yazınında {method} ile ulaşılan bulgularla büyük ölçüde örtüşmektedir.",
            "Bu sonuçlar, {field} yazınındaki bulgularla büyük ölçüde örtüşüyor.",
        ),
        "conclusion": (
            "Bu doğrultuda {topic}, {pop} için sürdürülebilir bir çerçevede yeniden değerlendirilmelidir.",
            "Bu nedenle {topic} konusunu {pop} açısından yeniden düşünmek gerekiyor.",
        ),
    },
    "literature_review": {
        "intro": (
            "Son on yılda {topic} konusundaki çalışmalar belirgin biçimde artmıştır.",
            "Son on yılda {topic} üzerine yapılan çalışmalar belirgin biçimde arttı.",
        ),
        "gap": (
            "Ancak bu çalışmaların önemli bir kısmı {tloc} yalnızca betimleyici göstergelere dayanmakta, nedensel ilişkileri ise sınırlı ölçüde ele almaktadır.",
            "Ancak bu çalışmaların önemli bir kısmı {tloc} yalnızca betimleyici göstergelere dayanıyor; nedensel ilişkileri ise sınırlı ölçüde ele alıyor.",
        ),
        "aim": (
            "Bu bölümde {field} yazınında {mgen} nasıl konumlandırıldığı karşılaştırmalı olarak değerlendirilmektedir.",
            "Bu bölümde {field} yazınında {mgen} nasıl konumlandırıldığını karşılaştırmalı olarak değerlendiriyoruz.",
        ),
        "method": (
            "İlgili kaynaklar {sloc} yürütülen çalışmalarla sınırlandırılmış, {method} kullanan araştırmalar ayrıca ele alınmıştır.",
            "İlgili kaynakları {sloc} yürütülen çalışmalarla sınırladık; {method} kullanan araştırmaları ayrıca ele aldık.",
        ),
        "finding": (
            "Yazın taraması, {tloc} iki rakip açıklamanın öne çıktığını göstermektedir.",
            "Yazın taraması {tloc} iki rakip açıklamanın öne çıktığını gösteriyor.",
        ),
        "discussion": (
            "Bu iki açıklama, {pgen} deneyimlerini farklı düzeylerde açıklamakta ve birbirini tamamlamaktadır.",
            "Bu iki açıklama {pgen} deneyimlerini farklı düzeylerde açıklıyor ve birbirini tamamlıyor.",
        ),
        "conclusion": (
            "Dolayısıyla {topic}, tek bir kuramsal çerçeveyle açıklanamayacak kadar çok boyutlu bir olgu olarak görülmelidir.",
            "Bu nedenle {topic} tek bir kuramsal çerçeveyle açıklanamayacak kadar çok boyutlu bir olgu olarak görülmeli.",
        ),
    },
    "methodology": {
        "intro": (
            "Araştırma, {method} temel alınarak tasarlanmıştır.",
            "Araştırmayı {method} temel alarak tasarladık.",
        ),
        "gap": (
            "Tasarım aşamasında {tgen} {sloc} nasıl gözlemleneceği ayrıntılı biçimde tanımlanmıştır.",
            "Tasarım aşamasında {tgen} {sloc} nasıl gözlemleneceğini ayrıntılı biçimde tanımladık.",
        ),
        "aim": (
            "Veri toplama süreci, {sloc} yürütülen ön incelemelerle desteklenmiştir.",
            "Veri toplama sürecini {sloc} yürütülen ön incelemelerle destekledik.",
        ),
        "method": (
            "Örneklem, {sloc} yer alan {pop} arasından ölçüt örnekleme yoluyla seçilmiştir.",
            "Örneklemi {sloc} yer alan {pop} arasından ölçüt örnekleme yoluyla seçtik.",
        ),
        "finding": (
            "Toplanan veriler iki araştırmacı tarafından bağımsız olarak kodlanmış ve kodlayıcılar arası uyum hesaplanmıştır.",
            "Toplanan verileri iki araştırmacı bağımsız olarak kodladı ve kodlayıcılar arası uyumu hesapladık.",
        ),
        "discussion": (
            "Analiz sürecinde {method} ile elde edilen sonuçlar, ham verilerle yeniden karşılaştırılmıştır.",
            "Analizde {method} ile elde ettiğimiz sonuçları ham verilerle yeniden karşılaştırdık.",
        ),
        "conclusion": (
            "Böylece {tgen} {sloc} gözlenen örüntülerin sistematik biçimde kaydedilmesi sağlanmıştır.",
            "Böylece {tgen} {sloc} gözlenen örüntüleri sistematik biçimde kaydettik.",
        ),
    },
    "findings": {
        "intro": (
            "Bulgular, {tloc} üç temel örüntünün varlığını ortaya koymaktadır.",
            "Bulgular {tloc} üç temel örüntünün varlığını ortaya koyuyor.",
        ),
        "gap": (
            "İlk örüntü, {pgen} {tdat} ilişkin beklentileriyle doğrudan ilişkilidir.",
            "İlk örüntü, {pgen} {tdat} ilişkin beklentileriyle doğrudan bağlantılı.",
        ),
        "aim": (
            "İkinci örüntü, {sloc} daha belirgin biçimde gözlenmiştir.",
            "İkinci örüntüyü {sloc} daha belirgin biçimde gözledik.",
        ),
        "method": (
            "Üçüncü örüntü ise {method} ile ulaşılan sonuçlarla sınırlıdır ve genellenmesi güçtür.",
            "Üçüncü örüntü ise {method} ile ulaştığımız sonuçlarla sınırlı; genellenmesi güç.",
        ),
        "finding": (
            "Beklenenin aksine, {tloc} olumlu yönde bir değişim gözlenmemiştir.",
            "Beklenenin aksine, {tloc} olumlu yönde bir değişim gözlemedik.",
        ),
        "discussion": (
            "Bu durum, {field} alanındaki yerleşik varsayımlarla çelişmektedir.",
            "Bu durum {field} alanındaki yerleşik varsayımlarla çelişiyor.",
        ),
        "conclusion": (
            "Genel olarak bulgular, {tgen} sanıldığı kadar homojen olmadığını göstermektedir.",
            "Genel olarak bulgular {tgen} sanıldığı kadar homojen olmadığını gösteriyor.",
        ),
    },
    "discussion": {
        "intro": (
            "Bu çalışmada elde edilen bulgular, {field} yazınındaki tartışmalarla yakından ilişkilidir.",
            "Bu çalışmada elde ettiğimiz bulgular {field} yazınındaki tartışmalarla yakından ilişkili.",
        ),
        "gap": (
            "Özellikle {tloc} gözlenen farklılık, {pgen} konumundan bağımsız olarak yorumlanmamalıdır.",
            "Özellikle {tloc} gözlediğimiz farklılığı {pgen} konumundan bağımsız olarak yorumlamamalıyız.",
        ),
        "aim": (
            "Bununla birlikte, {method} ile ulaşılan sonuçların {tgen} yalnızca bir kesitini yansıttığı unutulmamalıdır.",
            "Yine de {method} ile ulaştığımız sonuçların {tgen} yalnızca bir kesitini yansıttığını unutmamalıyız.",
        ),
        "method": (
            "Alan yazınında {tgen} benzer biçimde kavramsallaştırıldığı görülmektedir.",
            "Alan yazınında {topic} benzer biçimde kavramsallaştırılıyor.",
        ),
        "finding": (
            "Dolayısıyla ortaya çıkan tablo, tek bir neden-sonuç ilişkisinden çok, karşılıklı etkileşimlere işaret etmektedir.",
            "Dolayısıyla ortaya çıkan tablo tek bir neden-sonuç ilişkisinden çok karşılıklı etkileşimlere işaret ediyor.",
        ),
        "discussion": (
            "Bu yorum, {sloc} yürütülen benzer çalışmaların sonuçlarıyla da tutarlıdır.",
            "Bu yorum {sloc} yürütülen benzer çalışmaların sonuçlarıyla da tutarlı.",
        ),
        "conclusion": (
            "Bu bağlamda {topic}, {pop} açısından hem fırsatlar hem de yeni yükümlülükler yaratmaktadır.",
            "Bu nedenle {topic} {pop} açısından hem fırsatlar hem de yeni yükümlülükler yaratıyor.",
        ),
    },
    "conclusion": {
        "intro": (
            "Bu çalışma, {tgen} {field} açısından taşıdığı önemi gözler önüne sermektedir.",
            "Bu çalışma {tgen} {field} açısından taşıdığı önemi gözler önüne seriyor.",
        ),
        "gap": (
            "Araştırma soruları, {sloc} toplanan verilerle büyük ölçüde yanıtlanmıştır.",
            "Araştırma sorularını {sloc} topladığımız verilerle büyük ölçüde yanıtladık.",
        ),
        "aim": (
            "Ulaşılan sonuçlar, {method} kullanan sonraki çalışmalar için bir başlangıç noktası oluşturmaktadır.",
            "Ulaştığımız sonuçlar {method} kullanan sonraki çalışmalar için bir başlangıç noktası oluşturuyor.",
        ),
        "method": (
            "Bununla birlikte {tgen} tek bir kesitte incelenmesi, sonuçların genellenebilirliğini sınırlandırmaktadır.",
            "Ancak {tgen} yalnızca tek bir kesitte incelenmesi sonuçların genellenebilirliğini sınırlıyor.",
        ),
        "finding": (
            "Gelecek çalışmalarda {pgen} deneyimlerinin boylamsal olarak izlenmesi önerilmektedir.",
            "Gelecek çalışmalarda {pgen} deneyimlerini boylamsal olarak izlemeyi öneriyoruz.",
        ),
        "discussion": (
            "Sonuç olarak {topic}, {field} alanında disiplinler arası bir yaklaşım gerektirmektedir.",
            "Sonuç olarak {topic} {field} alanında disiplinler arası bir yaklaşım gerektiriyor.",
        ),
        "conclusion": (
            "Bu doğrultuda geliştirilecek politikaların {pgen} görüşleri doğrultusunda biçimlendirilmesi yerinde olacaktır.",
            "Bu doğrultuda geliştirilecek politikaları {pgen} görüşleri doğrultusunda biçimlendirmek yerinde olur.",
        ),
    },
    "limitations": {
        "intro": (
            "Bu çalışmanın birtakım sınırlılıkları bulunmaktadır.",
            "Bu çalışmanın bazı kısıtları var.",
        ),
        "gap": (
            "Öncelikle veriler, {sloc} yalnızca belirli bir dönemde toplanmıştır.",
            "Öncelikle verileri {sloc} yalnızca belirli bir dönemde topladık.",
        ),
        "aim": (
            "İkinci olarak {pgen} öz bildirimlerine dayanılması, yanıt yanlılığı riskini beraberinde getirmektedir.",
            "İkinci olarak {pgen} öz bildirimlerine dayandığımız için yanıt yanlılığı riski var.",
        ),
        "method": (
            "Ayrıca {method} ile ulaşılan sonuçlar, nedensel çıkarım yapmaya elverişli değildir.",
            "Ayrıca {method} ile ulaştığımız sonuçlar nedensel çıkarım yapmaya elverişli değil.",
        ),
        "finding": (
            "Örneklemin {sloc} toplanması, bulguların {field} alanının tamamına genellenmesini güçleştirmektedir.",
            "Örneklemi {sloc} topladığımız için bulguları {field} alanının tamamına genellemek güç.",
        ),
        "discussion": (
            "Bu sınırlılıklara karşın çalışma, {tgen} anlaşılmasına katkı sağlamaktadır.",
            "Bu kısıtlara karşın çalışma {tgen} anlaşılmasına katkı sağlıyor.",
        ),
        "conclusion": (
            "Gelecek araştırmaların daha geniş örneklemlerle ve farklı {unit_pl} üzerinde yürütülmesi önerilmektedir.",
            "Gelecek araştırmaları daha geniş örneklemlerle ve farklı {unit_pl} üzerinde yürütmeyi öneriyoruz.",
        ),
    },
    "abstract": {
        "intro": (
            "Bu çalışmada {topic}, {field} perspektifinden ele alınmıştır.",
            "Bu çalışmada {topic} konusunu {field} açısından ele aldık.",
        ),
        "gap": (
            "Araştırmanın amacı, {tloc} etkili olan temel etkenleri belirlemektir.",
            "Araştırmada {tloc} hangi temel etkenlerin etkili olduğunu belirlemeyi amaçladık.",
        ),
        "aim": (
            "Yöntem olarak {method} benimsenmiş, veriler {sloc} toplanmıştır.",
            "Yöntem olarak {method} benimsedik ve verileri {sloc} topladık.",
        ),
        "method": (
            "Örneklem, {sloc} yer alan {pop} arasından seçilmiştir.",
            "Örneklemi {sloc} yer alan {pop} arasından seçtik.",
        ),
        "finding": (
            "Bulgular, {tloc} anlamlı farklılıklar bulunduğunu göstermektedir.",
            "Bulgular {tloc} anlamlı farklılıklar olduğunu gösteriyor.",
        ),
        "discussion": (
            "Sonuçlar, {pgen} {tdat} ilişkin algılarının {field} bağlamında yeniden değerlendirilmesi gerektiğine işaret etmektedir.",
            "Sonuçlar, {pgen} {tdat} ilişkin algılarının {field} bağlamında yeniden değerlendirilmesi gerektiğine işaret ediyor.",
        ),
        "conclusion": (
            "Çalışma, {topic} konusunda hem kuramsal hem de uygulamalı katkı sunmaktadır.",
            "Çalışma {topic} konusunda hem kuramsal hem de uygulamalı katkı sunuyor.",
        ),
    },
    "ethics_statement": {
        "intro": (
            "Araştırma sürecinde {pgen} hakları ve gizliliği öncelikli olarak gözetilmiştir.",
            "Araştırma sürecinde {pgen} haklarını ve gizliliğini öncelikli olarak gözettik.",
        ),
        "gap": (
            "Veriler, {pop} ile yürütülen görüşmeler sırasında katılımcıların yazılı onamı alınarak toplanmıştır.",
            "Verileri {pop} ile yürüttüğümüz görüşmeler sırasında katılımcıların yazılı onamını alarak topladık.",
        ),
        "aim": (
            "Katılımcılara çalışmanın amacı ve kapsamı hakkında ayrıntılı bilgi verilmiştir.",
            "Katılımcılara çalışmanın amacı ve kapsamı hakkında ayrıntılı bilgi verdik.",
        ),
        "method": (
            "Kişisel veriler, kurumsal etik kurul ilkeleri doğrultusunda saklanmış ve üçüncü taraflarla paylaşılmamıştır.",
            "Kişisel verileri kurumsal etik kurul ilkeleri doğrultusunda sakladık ve üçüncü taraflarla paylaşmadık.",
        ),
        "finding": (
            "Çalışmaya katılım gönüllülük esasına dayanmış, katılımcılara istedikleri anda ayrılma hakkı tanınmıştır.",
            "Çalışmaya katılım gönüllülük esasına dayandı; katılımcılara istedikleri anda ayrılma hakkı tanıdık.",
        ),
        "discussion": (
            "Araştırma için ilgili üniversitenin etik kurulundan gerekli izin alınmıştır (Karar No: 2023/14).",
            "Araştırma için ilgili üniversitenin etik kurulundan gerekli izni aldık (Karar No: 2023/14).",
        ),
        "conclusion": (
            "Bu ilkeler doğrultusunda {topic} konusundaki çalışmaların etik açıdan şeffaf yürütülmesi beklenmektedir.",
            "Bu ilkeler doğrultusunda {topic} konusundaki çalışmaların etik açıdan şeffaf yürütülmesini bekliyoruz.",
        ),
    },
    "grant_proposal": {
        "intro": (
            "Önerilen proje, {tgen} {field} alanındaki güncel sorunlara çözüm üretmeyi hedeflemektedir.",
            "Önerilen proje {tgen} {field} alanındaki güncel sorunlara çözüm üretmeyi hedefliyor.",
        ),
        "gap": (
            "Projenin özgün değeri, {tloc} farklı paydaşların bakış açılarını birlikte ele almasından kaynaklanmaktadır.",
            "Projenin özgün değeri, {tloc} farklı paydaşların bakış açılarını birlikte ele almasından kaynaklanıyor.",
        ),
        "aim": (
            "Proje kapsamında {sloc} iki yıl süreyle {method} uygulanacaktır.",
            "Proje kapsamında {sloc} iki yıl boyunca {method} uygulayacağız.",
        ),
        "method": (
            "Beklenen çıktılar arasında bir rapor, iki makale ve {pop} için hazırlanmış bir rehber yer almaktadır.",
            "Beklenen çıktılar arasında bir rapor, iki makale ve {pop} için hazırlanmış bir rehber var.",
        ),
        "finding": (
            "Projenin toplam bütçesi 1.250.000 TL olarak öngörülmektedir.",
            "Projenin toplam bütçesini 1.250.000 TL olarak öngörüyoruz.",
        ),
        "discussion": (
            "Proje, {topic} konusunda ulusal kapasiteyi güçlendirmeye katkı sağlayacaktır.",
            "Proje {topic} konusunda ulusal kapasiteyi güçlendirmeye katkı sağlayacak.",
        ),
        "conclusion": (
            "Bu nedenle projenin desteklenmesi, {field} alanında uzun vadeli bir etki yaratabilir.",
            "Bu nedenle projenin desteklenmesi {field} alanında uzun vadeli bir etki yaratabilir.",
        ),
    },
    "conference_abstract": {
        "intro": (
            "Bu bildiride {topic}, {field} alanındaki güncel gelişmeler ışığında ele alınmaktadır.",
            "Bu bildiride {topic} konusunu {field} alanındaki güncel gelişmeler ışığında ele alıyoruz.",
        ),
        "gap": (
            "Sunumun amacı, {tloc} öne çıkan iki yaklaşımı karşılaştırmaktır.",
            "Sunumda {tloc} öne çıkan iki yaklaşımı karşılaştırmayı amaçlıyoruz.",
        ),
        "aim": (
            "Çalışmada {method} kullanılmış ve veriler {sloc} toplanmıştır.",
            "Çalışmada {method} kullandık ve verileri {sloc} topladık.",
        ),
        "method": (
            "Ön bulgular, {pgen} {tdat} ilişkin algılarının önemli ölçüde farklılaştığını göstermektedir.",
            "Ön bulgular {pgen} {tdat} ilişkin algılarının önemli ölçüde farklılaştığını gösteriyor.",
        ),
        "finding": (
            "Bildiri, {topic} konusunda tartışma açmayı ve geri bildirim toplamayı hedeflemektedir.",
            "Bildiri {topic} konusunda tartışma açmayı ve geri bildirim toplamayı hedefliyor.",
        ),
        "discussion": (
            "Katılımcıların {tloc} ilişkin deneyimleri, oturum sonunda ayrıntılı olarak paylaşılacaktır.",
            "Katılımcıların {tloc} ilişkin deneyimlerini oturum sonunda ayrıntılı olarak paylaşacağız.",
        ),
        "conclusion": (
            "Bu çalışma, {field} alanındaki uygulamalara somut öneriler sunmaktadır.",
            "Bu çalışma {field} alanındaki uygulamalara somut öneriler sunuyor.",
        ),
    },
    "peer_review": {
        "intro": (
            "Değerlendirilen çalışma, {topic} konusunu {field} çerçevesinde ele almaktadır.",
            "Değerlendirdiğim çalışma {topic} konusunu {field} çerçevesinde ele alıyor.",
        ),
        "gap": (
            "Yazarlar, {tloc} var olan yazını büyük ölçüde gözden kaçırmıştır.",
            "Yazarlar {tloc} var olan yazını büyük ölçüde gözden kaçırmış.",
        ),
        "aim": (
            "Kuramsal çerçeve genel hatlarıyla tutarlı olmakla birlikte, {tgen} tanımı yeterince açık değildir.",
            "Kuramsal çerçeve genel hatlarıyla tutarlı, ancak {tgen} tanımı yeterince açık değil.",
        ),
        "method": (
            "Yöntem bölümünde {method} tercih edilmesi yerinde olmakla birlikte, örneklem büyüklüğü gerekçelendirilmemiştir.",
            "Yöntem bölümünde {method} tercih edilmesi yerinde, ancak örneklem büyüklüğü gerekçelendirilmemiş.",
        ),
        "finding": (
            "Bulguların sunumu, {tloc} gözlenen farklılıkların kaynağını açıklamakta yetersiz kalmaktadır.",
            "Bulguların sunumu {tloc} gözlenen farklılıkların kaynağını açıklamakta yetersiz kalıyor.",
        ),
        "discussion": (
            "Yazarlardan, {pgen} görüşlerine dayanan yorumları verilerle daha açık biçimde ilişkilendirmeleri beklenmektedir.",
            "Yazarlardan {pgen} görüşlerine dayanan yorumları verilerle daha açık biçimde ilişkilendirmelerini bekliyoruz.",
        ),
        "conclusion": (
            "Çalışmanın bu haliyle yayımlanmadan önce önemli düzeltmeler yapılması gerekmektedir.",
            "Çalışmanın bu haliyle yayımlanmadan önce önemli düzeltmeler yapılması gerekiyor.",
        ),
    },
}

# Numeric / citation / URL / abbreviation sentences. One is appended to every
# fourth sample, cycling through five formats so all protected-span kinds appear.
_QUANT: list[str] = [
    "Katılımcıların %63'ü {tloc} belirgin bir iyileşme bildirirken, bu oran 2019 yılında %41 düzeyinde kalmıştır.",
    "Elde edilen sonuçlar, {tloc} gözlenen eğilimin daha önce bildirilen bulgularla tutarlı olduğunu göstermektedir (Yılmaz, 2019; Demir vd., 2021).",
    "Benzer bir örüntü {field} yazınında da raporlanmıştır \\cite{kaya2021,ozturk2020}.",
    "Ayrıntılı veri setine https://example.org/veri/2023 adresinden erişilebilir (bkz. Ek 1, ss. 14-22).",
    "Ölçümler 2018-2022 yılları arasında toplanmış; eksik veriler vb. nedenlerle 37 gözlem analiz dışında bırakılmıştır.",
]

# An ethics statement cannot report "our participants improved", and a reviewer
# does not own the participants; both keep only the citation/URL/abbreviation
# formats that fit their voice.
_QUANT_ALLOWED: dict[str, tuple[int, ...]] = {
    "ethics_statement": (2, 3),
    "peer_review": (2, 3, 4),
}

_PLANS: list[tuple[str, ...]] = [
    ("intro", "gap", "method", "finding", "discussion", "conclusion"),
    ("intro", "gap", "method", "finding", "conclusion"),
    ("intro", "method", "finding", "conclusion"),
    ("intro", "gap", "finding", "discussion", "conclusion"),
]

_STYLES = ("nominal", "plain", "mixed")


def _render(template: str, domain: dict[str, str]) -> str:
    # str.format would choke on the LaTeX backslash, so only substitute slots.
    out = template
    for key, value in domain.items():
        out = out.replace("{" + key + "}", value)
    return out


def _build() -> tuple[list[str], list[dict]]:
    samples: list[str] = []
    meta: list[dict] = []
    for reg_index, register in enumerate(REGISTERS):
        bank = _SENTENCES[register]
        for j in range(22):
            domain = DOMAINS[(j + reg_index) % len(DOMAINS)]
            plan = _PLANS[j % len(_PLANS)]
            has_quant = j % 4 == 0
            if has_quant and len(plan) == 6:
                # Keep the paragraph within the 3-6 sentence window after the
                # numeric sentence is inserted.
                plan = ("intro", "gap", "method", "finding", "conclusion")
            style = _STYLES[(j // 8) % len(_STYLES)]
            sentences: list[str] = []
            for role_index, role in enumerate(plan):
                heavy, plain = bank[role]
                if style == "nominal":
                    template = heavy
                elif style == "plain":
                    template = plain
                else:
                    template = heavy if role_index % 2 == 0 else plain
                sentences.append(_render(template, domain))
            if has_quant:
                allowed = _QUANT_ALLOWED.get(register, range(len(_QUANT)))
                quant = _QUANT[allowed[(j // 4) % len(allowed)]]
                sentences.insert(-1, _render(quant, domain))
            samples.append(" ".join(sentences))
            meta.append({
                "register": register,
                "domain": domain["domain"],
                "style": style,
                "has_protected": has_quant,
            })
    return samples, meta


SAMPLES: list[str] = []
SAMPLE_META: list[dict] = []
SAMPLES, SAMPLE_META = _build()

assert len(SAMPLES) == len(SAMPLE_META)
